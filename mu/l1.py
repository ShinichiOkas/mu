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
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Sequence

# ツール = (呼び出せる関数, 使い方テキスト)
Tool = tuple[Callable[..., Any], str]

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

        for tc in calls:
            name = tc.function.name
            args = dict(tc.function.arguments or {})
            result = _invoke(dispatch, name, args)
            messages.append({"role": "tool", "tool_name": name, "content": str(result)})
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
        if not tools:
            return list(messages)
        return [{"role": "system", "content": _system_content(tools)}, *messages]


def _invoke(dispatch: dict, name: str, args: dict) -> Any:
    func = dispatch.get(name)
    if func is None:
        return f"error: unknown tool '{name}'"
    kept, dropped = _bind_to_signature(func, args)
    try:
        result = func(**kept)
    except Exception as e:  # ツールの失敗は結果として model に返す（回復可能に）
        return f"error: {e}"
    if dropped:
        # モデルがスキーマにない引数を幻覚しても、正しい引数で実行し、落としたことだけ
        # 注記する。厳格な func(**args) は余計な1引数で正しい呼び出しごと落とし、弱い
        # モデルを無限ループさせていた（実ログで観測）。落とすのは判断でなく実行の頑健化。
        return f"{result}\n[note] ignored unknown arguments: {sorted(dropped)}"
    return result


def _bind_to_signature(func: Callable, args: dict) -> tuple[dict, set]:
    """モデルが渡した引数を関数シグネチャに束縛する。未知の kwarg は落とす。

    **kwargs を受ける関数はそのまま通す（何も落とさない）。
    """
    params = inspect.signature(func).parameters
    if any(p.kind is p.VAR_KEYWORD for p in params.values()):
        return dict(args), set()
    kept = {k: v for k, v in args.items() if k in params}
    return kept, set(args) - set(kept)
