"""L2 — PDCA / Reflect ループ（エージェント）。

L1 の上に「ゴールに向かって自立実行する」層を重ねる。PDCA のうち **D は L1**。
L2 が足すのは **Reflect（Check ＋ Act）** ただ一つ:

    loop（呼び出し側が規定する上限まで）:
      D       : L1 を l1_max 回まで回す（ゴールに向かって行動）
      Reflect : 「ゴールは達成されたか？ 未達なら何が足りないか」を構造化出力で1回問う
      判定    : 合格 → 終了 ／ 未達 → next を再投入して継続（＝そこで計画が生まれる）

**再帰同一構造**: この「内側ループを回す → Reflect → 続行/停止」は、L3 が L2 を
管理するときも同じ形になる。再帰の底（最上位の停止）は人間。

**無状態**: 状態は messages（上位が持つ）。上限（max_rounds / l1_max）は自層に
ハードコードせず、呼び出し側（l2_chat / テスト / 将来の L3）が規定する。
"""

from __future__ import annotations

import json
from typing import Any, Sequence

from .l1 import ToolLoop, Tool

# Reflect の合否判定を確実に取るための構造化出力スキーマ。
_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "passed": {"type": "boolean"},
        "reason": {"type": "string"},
        "next": {"type": "string"},
    },
    "required": ["passed", "reason", "next"],
}

_REFLECT_SYSTEM = (
    "You are a strict but FAIR verifier. Given a GOAL and the TRANSCRIPT of an agent's "
    "attempt, decide whether the goal is achieved. Judge ONLY against the constraints "
    "explicitly stated in the GOAL. Do NOT invent extra requirements the goal does not "
    "mention (e.g. trailing whitespace, or the letter-case of a filename on a "
    "case-insensitive OS). If the transcript clearly shows the stated constraints are met, "
    "PASS. If the result cannot be verified from the transcript (e.g. a file was written "
    "but its content is not shown), do not pass; set next to instruct the agent to reveal "
    "the concrete evidence (e.g. read the file back and show its full content). "
    "Reply as JSON: passed (bool), reason (short), next (a concrete next action if not "
    "passed; empty string if passed)."
)

# L2 が再投入する制御フィードバックの目印。L1 には見せる（user ロールで steering）が、
# 次の Reflect の transcript からは除外する（「未達」表明を失敗の証拠と誤読させないため）。
_FEEDBACK_PREFIX = "[L2] "

# verdict の next が空・壊れているときの中立指示（L1 を証拠提示へ導く）。
_NEUTRAL_NEXT = "ゴールが満たされている具体的な証拠を示すこと（例: 対象ファイルを読み返して内容を表示する）。"


class Agent:
    """L2。L1（D）を Reflect（C＋A）で包み、ゴール達成まで回す。"""

    def __init__(self, l0: Any, l1: Any = None) -> None:
        self._l0 = l0                                   # Reflect（構造化 chat）に使う
        self._l1 = l1 if l1 is not None else ToolLoop(l0)  # D に使う

    def run(
        self,
        model: str,
        goal: str,
        tools: Sequence[Tool],
        *,
        system: str | None = None,
        max_rounds: int = 6,
        l1_max: int = 10,
    ) -> tuple[list, bool]:
        messages: list = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": goal})

        for _ in range(max_rounds):
            messages, v = self.step(model, messages, goal, tools, l1_max=l1_max)
            if v["passed"]:
                return messages, True
        return messages, False

    def step(
        self,
        model: str,
        messages: list,
        goal: str,
        tools: Sequence[Tool],
        *,
        l1_max: int = 10,
    ) -> tuple[list, dict]:
        """ループを1周進める: D（L1）→ Reflect（C＋A）。(messages, verdict) を返す。

        未達なら next を messages に再投入する。周と周の境目で上位が中断/再開できる。
        """
        messages = self._l1.run(model, messages, tools, max_rounds=l1_max)  # D
        v = self._reflect(model, goal, messages)                            # C ＋ A
        if not v["passed"]:
            # user ロールで戻す（L1 が確実に読む＝steering）。目印を付け、次の Reflect の
            # transcript からは除外する（未達表明を失敗の証拠と誤読させない＝汚染防止）。
            nxt = v["next"] or _NEUTRAL_NEXT  # 空の next では steering にならない
            messages.append(
                {"role": "user", "content": _FEEDBACK_PREFIX + f"まだゴールは達成できていません。次にやること: {nxt}"}
            )
        return messages, v

    def _reflect(self, model: str, goal: str, messages: list) -> dict:
        reflect_messages = [
            {"role": "system", "content": _REFLECT_SYSTEM},
            {"role": "user", "content": f"GOAL:\n{goal}\n\nTRANSCRIPT:\n{transcript(messages)}"},
        ]
        # think=False: 思考の混入で JSON が壊れるのを防ぐ（構造化出力を安定させる）。
        resp = self._l0.chat(model, reflect_messages, format=_VERDICT_SCHEMA, think=False)
        return _parse_verdict(resp.message.content)


def transcript(messages: list, limit: int = 6000) -> str:
    """messages を検証者向けの読みやすいテキストに畳む（末尾優先で上限）。

    L2 の Reflect と L3 の失敗分析が共用する公開ヘルパ（層をまたいで使う）。
    """
    parts = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "system":
            continue
        if role == "tool":
            parts.append(f"[tool {m.get('tool_name')}] {content}")
        elif role == "assistant":
            if m.get("tool_calls"):
                names = ", ".join(tc["function"]["name"] for tc in m["tool_calls"])
                parts.append(f"assistant: (calls {names})")
            if content:
                parts.append(f"assistant: {content}")
        elif role == "user":
            if content.startswith(_FEEDBACK_PREFIX):
                continue  # L2 の制御フィードバックは検証者に見せない
            parts.append(f"user: {content}")
    text = "\n".join(parts)
    return text[-limit:]


def _parse_verdict(content: str) -> dict:
    text = content or ""
    candidates = [text]
    # ```json ... ``` や thinking 混じりに備え、最初の { 〜 最後の } も候補にする。
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])
    for c in candidates:
        try:
            data = json.loads(c)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict) and "passed" in data:
            return {
                "passed": bool(data.get("passed", False)),
                "reason": str(data.get("reason", "")),
                "next": str(data.get("next", "")),
            }
    # 壊れていたら未達扱い（安全側）。next は L1 を証拠提示へ導く中立指示にする。
    return {"passed": False, "reason": "unparseable verdict", "next": _NEUTRAL_NEXT}
