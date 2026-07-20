r"""l1_chat.py — L1（ツールコールのループ）を触る最小 CLI チャット。

L1 = L0 の上でツールコールを回す層。ツールは tools.py の検証用5種
（read_file / write_file / edit_file / list_dir / execute_command）を登録してある。
「mu_demo.txt に hello と書いて」「execute_command で dir を実行して」等を頼むと、
モデルがツールを呼び、mu が実行して結果を戻し、モデルが答える。

ループは step() を上限（MAX_ROUNDS。上限は呼び出し側＝この CLI が規定）まで回す形で
駆動し、実行されたツールをその場で表示する。会話履歴は CLI 側が持つ（L1 は無状態）。
中断は Ctrl-C。

注意: execute_command / write_file / edit_file は実ファイル・実シェルに触れる。

使い方:
    .\.venv\Scripts\python.exe l1_chat.py [model]
既定モデルは qwen3.5:9b（tool 対応）。gemma3 系は tools 非対応なので不可。
"""

import os
import platform
import sys

from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from tools import TOOLS

# Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_MODEL = "qwen3.5:9b"  # 参照モデル（他は gemma4:12b）
MAX_ROUNDS = 32  # ループ上限（呼び出し側が規定）。無限ツールコールの暴走を打ち切る


def _env_preamble() -> str:
    """呼び出し側が与える環境の地面（C: 環境吸収は呼び出し側＋ツールの責務）。"""
    return (
        "Environment:\n"
        f"- OS: {platform.system()} {platform.release()}\n"
        f"- Working directory: {os.getcwd()}\n"
        "- execute_command runs in PowerShell — use PowerShell/Windows syntax "
        "(e.g. Get-ChildItem, Get-Content), not Unix commands like ls/cat.\n"
        "- Use list_dir to discover files instead of guessing paths."
    )


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    l1 = ToolLoop(OllamaInterface())
    messages: list = [{"role": "system", "content": _env_preamble()}]

    names = ", ".join(func.__name__ for func, _ in TOOLS)
    print(f"L1 chat / model={model}  tools: {names}  (/exit で終了)")
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
            done = False
            for _ in range(MAX_ROUNDS):
                mark = len(messages)
                messages, done = l1.step(model, messages, TOOLS)
                for m in messages[mark:]:  # この周で実行されたツールを表示
                    if m.get("role") == "tool":
                        print(f"  [tool] {m['tool_name']} -> {m['content']}")
                if done:
                    break
            if not done:
                print(f"  [!] {MAX_ROUNDS} 周の上限に達したため打ち切りました")
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        print(f"bot> {messages[-1].get('content', '')}")


if __name__ == "__main__":
    main()
