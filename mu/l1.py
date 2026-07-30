"""L1 — ツールコールのループ。

L0 の上に「行動する層（Do）」を1枚重ねる。本質はこれだけ:

    chat → 返答に tool_call あり → ツール実行 → 結果を付けて chat → ループ
                                → tool_call なし → 終わり

**無状態**。状態（＝messages）は上位が持つ。
- 中断 = 上位が step を呼ぶのをやめる
- 再開 = 保存した messages で step を呼ぶ
いずれも「周と周の境目」で起きる（ツール実行の途中では止めない）。

ツールは `(func, usage_text)` のペアのリストで渡す。L1 はここから 3 つを導出する:
1. system prompt へ usage_text を束ねて注入（汎用化・弱いモデルへの誘導）
2. `chat(tools=[func, ...])` の構造化スキーマ（tool_calls を確実に受け取る。
   関数→スキーマは公式ライブラリが自動生成）
3. dispatch `{func.__name__: func}`（実行するのは mu 側）

**構造化 tool 結果**（合意005）: ツールは str のほか `ToolResult` を返せる。
content（モデル向け散文）と別に ok / facts（機械可読な事実。ディスクの stat・
exit code 等、実体から作る）を持ち、tool メッセージに保持される。facts / ok は
検証者（L2 Reflect・L3 analyze）向けのチャネルで、モデルへ送る形からは剥がす
— 判定を「表象」でなく「実体」に寄せるための別チャネル。
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

# ツール = (呼び出せる関数, 使い方テキスト)
Tool = tuple[Callable[..., Any], str]


@dataclass
class ToolResult:
    """ツール実行の結果。content は散文、ok / facts は実体からの機械可読な事実。"""

    content: str
    ok: bool = True
    facts: dict = field(default_factory=dict)

_TOOLS_HEADER = (
    "You have access to the tools listed below. "
    "Whenever the user's request can be handled by one of these tools, "
    "you MUST call the appropriate tool instead of answering from memory or guessing. "
    "Available tools:"
)


def _system_content(tools: Sequence[Tool]) -> str:
    lines = [_TOOLS_HEADER]
    lines.extend(f"- {usage}" for _func, usage in tools)
    return "\n".join(lines)


def _assistant_dict(message: Any) -> dict:
    """L0 の応答メッセージを、再送可能な素の dict にして返す。"""
    d: dict = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        d["tool_calls"] = [
            {"function": {"name": tc.function.name, "arguments": dict(tc.function.arguments or {})}}
            for tc in message.tool_calls
        ]
    return d


class ToolLoop:
    """L1。L0（理想化された chat）の上でツールコールを回す無状態のループ。"""

    def __init__(self, l0: Any) -> None:
        self._l0 = l0

    def step(self, model: str, messages: list, tools: Sequence[Tool]) -> tuple[list, bool]:
        """ループを 1 周進める。(messages, done) を返す。done = tool_call が無かった。"""
        dispatch = {func.__name__: func for func, _ in tools}
        send = self._with_system(messages, tools)
        resp = self._l0.chat(model, send, tools=[func for func, _ in tools] or None)
        message = resp.message

        messages.append(_assistant_dict(message))
        calls = message.tool_calls or []
        if not calls:
            return messages, True

        usages = {func.__name__: usage for func, usage in tools}
        for tc in calls:
            name = tc.function.name
            args = dict(tc.function.arguments or {})
            r = _invoke(dispatch, usages, name, args)
            messages.append(
                {"role": "tool", "tool_name": name, "content": r.content, "ok": r.ok, "facts": r.facts}
            )
        return messages, False

    def run(self, model: str, messages: list, tools: Sequence[Tool], max_rounds: int = 32) -> list:
        """done になるまで step を回す薄いループ。"""
        done = False
        rounds = 0
        while not done and rounds < max_rounds:
            messages, done = self.step(model, messages, tools)
            rounds += 1
        return messages

    @staticmethod
    def _with_system(messages: list, tools: Sequence[Tool]) -> list:
        # system 注入は毎周その場で組み立て、永続 messages には残さない（無状態）。
        # 呼び出し側が先頭に system（環境プリアンブル等）を持つ場合は 1 枚に併合する
        # （多くのモデルテンプレートは先頭 1 枚の system を想定するため）。
        # facts / ok は検証者向けチャネルなので、モデルへ送る形からは剥がす。
        msgs = [_model_view(m) for m in messages]
        if not tools:
            return msgs
        content = _system_content(tools)
        if msgs and msgs[0].get("role") == "system":
            merged = {"role": "system", "content": f"{content}\n\n{msgs[0]['content']}"}
            return [merged, *msgs[1:]]
        return [{"role": "system", "content": content}, *msgs]


def _model_view(m: dict) -> dict:
    """モデルへ送るメッセージ形。tool メッセージから facts / ok を剥がす。"""
    if m.get("role") == "tool" and ("facts" in m or "ok" in m):
        return {"role": "tool", "tool_name": m.get("tool_name"), "content": m.get("content", "")}
    return m


def _invoke(dispatch: dict, usages: dict, name: str, args: dict) -> ToolResult:
    func = dispatch.get(name)
    if func is None:
        return ToolResult(f"error: unknown tool '{name}'", ok=False)
    kept, dropped = _bind_to_signature(func, args)
    missing = _missing_required(func, kept)
    if missing:
        # 必須引数の欠落は実行せず手前で止め、usage と受領引数をエコーして steering する。
        # 素の TypeError 文字列だけでは弱いモデルが同じ呼び出しを繰り返す
        # （F1 実走で write_file の path 欠けが偽・完遂の第1因子になった）。
        return ToolResult(
            f"error: missing required argument(s) {missing} for {name}.\n"
            f"usage: {usages.get(name, name)}\n"
            f"received arguments: {sorted(kept)} — call again with ALL required arguments.",
            ok=False,
        )
    try:
        result = func(**kept)
    except Exception as e:  # ツールの失敗は結果として model に返す（回復可能に）
        return ToolResult(f"error: {e}", ok=False)
    r = _normalize(result)
    if dropped:
        # モデルがスキーマにない引数を幻覚しても、正しい引数で実行し、落としたことだけ
        # 注記する。厳格な func(**args) は余計な1引数で正しい呼び出しごと落とし、弱い
        # モデルを無限ループさせていた（実ログで観測）。落とすのは判断でなく実行の頑健化。
        r = ToolResult(
            f"{r.content}\n[note] ignored unknown arguments: {sorted(dropped)}", ok=r.ok, facts=r.facts
        )
    return r


def _normalize(result: Any) -> ToolResult:
    """ツールの返り値を ToolResult に正規化する。素の値は従来契約（"error:" 接頭辞）で判定。"""
    if isinstance(result, ToolResult):
        return result
    text = str(result)
    return ToolResult(text, ok=not text.startswith("error:"))


def _missing_required(func: Callable, kept: dict) -> list:
    """束縛後になお欠けている必須引数名を返す（デフォルト無しの位置/キーワード引数）。"""
    params = inspect.signature(func).parameters
    return [
        p.name
        for p in params.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        and p.default is p.empty
        and p.name not in kept
    ]


def _bind_to_signature(func: Callable, args: dict) -> tuple[dict, set]:
    """モデルが渡した引数を関数シグネチャに束縛する。未知の kwarg は落とす。

    **kwargs を受ける関数はそのまま通す（何も落とさない）。
    """
    params = inspect.signature(func).parameters
    if any(p.kind is p.VAR_KEYWORD for p in params.values()):
        return dict(args), set()
    kept = {k: v for k, v in args.items() if k in params}
    return kept, set(args) - set(kept)
