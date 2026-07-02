r"""l0_chat.py — L0 を直接触るための最小 CLI チャット。

L0（Ollama インタフェース層）だけを使う。ツールも PDCA も無い、
「理想化された chat」をそのまま叩くだけの REPL。会話履歴は CLI 側が持つ
（L0 は無状態のまま）。L0 の 4 型エラーはそのまま表示して挙動を体感できる。

使い方:
    .\.venv\Scripts\python.exe l0_chat.py [model]
既定モデルは gemma3:1b。/exit または Ctrl-C で終了。
"""

import sys

from mu.l0 import OllamaInterface, L0Error

DEFAULT_MODEL = "gemma3:1b"

# Windows コンソール等の既定エンコーディング（cp932 等）でも日本語・記号で
# 落ちないよう、入出力を UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    l0 = OllamaInterface()
    messages: list[dict] = []

    print(f"L0 chat / model={model}  (/exit で終了)")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user in ("/exit", "/quit"):
            break
        if not user:
            continue

        messages.append({"role": "user", "content": user})
        try:
            resp = l0.chat(model, messages)
        except L0Error as e:
            # 接続を理想化しても吸収し切れなかった失敗は 4 型で届く。
            print(f"[L0:{type(e).__name__}] {e}")
            messages.pop()  # 送れなかった発話は履歴から戻す
            continue

        content = resp.message.content
        print(f"bot> {content}")
        messages.append({"role": "assistant", "content": content})


if __name__ == "__main__":
    main()
