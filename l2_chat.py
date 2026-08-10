r"""l2_chat.py — L2（PDCA / Reflect ループ）を触る最小 CLI。

L2 = L1（D）を Reflect（C＋A）で包み、与えたゴールに向かって自立実行する層。
入力は1行の「ゴール」。エージェントが `D → Reflect → 続行/停止` を繰り返し、
各周のツール実行と Reflect 判定（合否＋理由）を表示する。

上限（MAX_ROUNDS / L1_MAX）はこの呼び出し側が規定する（L2 は policy を持たない）。
最上位の停止は人間（Ctrl-C）。会話履歴は CLI 側が持つ（L2 は無状態）。

使い方:
    .\.venv\Scripts\python.exe l2_chat.py [model]
既定モデルは qwen3.5:9b（tool 対応）。
"""

import sys

from chat_common import env_preamble, short, utf8_console
from mu.l0 import OllamaInterface, L0Error
from mu.l2 import Agent
from tools import TOOLS

utf8_console()

DEFAULT_MODEL = "qwen3.5:9b"  # 参照モデル（他は gemma4:12b）
MAX_ROUNDS = 5   # L2 の上限（呼び出し側が規定）
L1_MAX = 10      # 1 周で L1 を回す上限


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    agent = Agent(OllamaInterface())

    print(f"L2 chat / model={model}  max_rounds={MAX_ROUNDS}  (ゴールを入力 / /exit で終了)")
    while True:
        try:
            goal = input("goal> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if goal in ("/exit", "/quit"):
            break
        if not goal:
            continue

        messages: list = [
            {"role": "system", "content": env_preamble()},
            {"role": "user", "content": goal},
        ]
        passed = False
        try:
            for r in range(1, MAX_ROUNDS + 1):
                mark = len(messages)
                messages, verdict = agent.step(model, messages, goal, TOOLS, l1_max=L1_MAX)
                for m in messages[mark:]:
                    if m.get("role") == "tool":
                        print(f"  [tool] {m['tool_name']} -> {short(m['content'])}")
                print(f"  [reflect {r}] passed={verdict['passed']} :: {short(verdict['reason'], 160)}")
                if verdict["passed"]:
                    passed = True
                    break
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        final = next(
            (m["content"] for m in reversed(messages)
             if m.get("role") == "assistant" and m.get("content")),
            "",
        )
        print(f"{'✓ DONE' if passed else '✗ 上限で打ち切り'}")
        print(f"bot> {final}")


if __name__ == "__main__":
    main()
