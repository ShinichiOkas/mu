r"""l3_chat.py — L3（大域 Plan / 複雑タスクの完遂）を触る最小 CLI。

L3 = L2 を"単位"として組み合わせ、複雑ゴールを完遂する層。PDCA が完全体で
現れ、P（初回 Plan）と A（再計画）は **HITL 承認スロット**に上がる。この CLI
では承認者＝人間（あなた）。Plan / 再計画のたびに単位一覧を表示し、
    y      = 承認して実行
    d N    = 単位 N を削除（過剰な単位を落として続行）
    n      = 中断
を受ける。D・C（各単位の L2 実行と合否判定）は自律。

上限（MAX_ROUNDS / L2_MAX / L2_L1_MAX）はこの呼び出し側が規定する
（L3 は policy を持たない）。成果物は実ファイルとして cwd に生成される
（file grounding）。ワーキングディレクトリ破壊を避けるため、使い捨ての
ディレクトリで実行すること。

使い方:
    .\.venv\Scripts\python.exe l3_chat.py [model]
既定モデルは qwen3.5:9b（参照モデル。もう一つは gemma4:12b）。
"""

import os
import platform
import sys

from mu.l0 import OllamaInterface, L0Error
from mu.l3 import Orchestrator
from tools import TOOLS

# Windows コンソール等でも日本語・記号で落ちないよう UTF-8 にそろえる。
for _stream in (sys.stdout, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

DEFAULT_MODEL = "qwen3.5:9b"  # 参照モデル（他は gemma4:12b）
MAX_ROUNDS = 8   # L3 の上限（呼び出し側が規定）
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限


class _Abort(Exception):
    """人間が承認を拒否して run を止める（HITL の中断）。"""


def _short(text: object, n: int = 120) -> str:
    s = str(text or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _show_units(units: list) -> None:
    if not units:
        print("  (単位なし)")
    for i, u in enumerate(units, 1):
        mark = "x" if u.get("done") else " "
        print(f"  {i}. [{mark}] {u.get('file')}")
        print(f"        task: {_short(u.get('task'))}")
        print(f"        基準: {_short(u.get('criterion'))}")


def _approve(units: list) -> list:
    """HITL: Plan / 再計画を表示し、承認(y) / 削除(d N) / 中断(n) を受ける。"""
    units = [dict(u) for u in units]  # 破壊しないコピーを編集する
    while True:
        print("── 承認する Plan ──")
        _show_units(units)
        try:
            cmd = input("承認 [y=実行 / d N=単位N削除 / n=中断] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise _Abort()
        if cmd == "y":
            return units
        if cmd == "n":
            raise _Abort()
        if cmd.startswith("d"):
            arg = cmd[1:].strip()
            if arg.isdigit() and 1 <= int(arg) <= len(units):
                removed = units.pop(int(arg) - 1)
                print(f"  -> 削除: {removed.get('file')}")
            else:
                print("  ? 使い方: d <番号>（1〜{}）".format(len(units)))
            continue
        print("  ? y / d N / n のいずれかを入力")


def _log(event: tuple) -> None:
    """自律部（D・C）の進行を表示。plan/replan は _approve が対話表示するので出さない。"""
    kind = event[0]
    if kind == "unit_done":
        print(f"  [x] UNIT DONE  : {event[1].get('file')}")
    elif kind == "unit_failed":
        analysis = event[2]
        print(f"  [!] UNIT FAILED: {event[1].get('file')} -> {_short(analysis.get('reason'))}")
        if analysis.get("suggestion"):
            print(f"      suggestion : {_short(analysis.get('suggestion'))}")
    elif kind == "overall":
        v = event[1]
        print(f"  [=] OVERALL: passed={v.get('passed')} :: {_short(v.get('reason'), 160)}")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    orch = Orchestrator(OllamaInterface())

    print(f"L3 chat / model={model}  max_rounds={MAX_ROUNDS}  (複雑ゴールを入力 / /exit で終了)")
    print(f"  cwd={os.getcwd()}  <- 成果物ファイルはここに作られます")
    print("  環境:", platform.system(), platform.release(), "/ execute_command=PowerShell")
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

        try:
            result = orch.run(
                model, goal, TOOLS,
                approve=_approve, log=_log,
                max_rounds=MAX_ROUNDS, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except _Abort:
            print("— 中断しました")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        print(f"=== {'完遂 ✓' if result['done'] else '未達 ✗（上限到達）'} ===")
        for u in result["units"]:
            print(f"  {'[x]' if u.get('done') else '[ ]'} {u.get('file')}")


if __name__ == "__main__":
    main()
