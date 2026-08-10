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

実行中は各層の動きをその場で実況する（層はインデントで入れ子表示）:
    [L3] Plan/失敗分析/全体判定  [L2] Reflect 判定  [L1] 思考  [tool] ツール実行
LLM 呼び出しは開始時に行を出し、完了時に所要秒数を追記する。表示のない沈黙は
ない（沈黙して見える間＝行末が開いている間はローカル LLM が推論中）。
表示は CLI の責務であり、mu の各層は無変更・無関知（実況の実体は chat_common）。

使い方:
    .\.venv\Scripts\python.exe l3_chat.py [model]
既定モデルは gemma4:12b（参照モデル。もう一つは qwen3.5:9b）。
"""

import os
import platform
import sys

from chat_common import Abort, VerboseL0, env_preamble, short, utf8_console, verbose_tools
from mu.l0 import OllamaInterface, L0Error
from mu.l2 import Agent
from mu.l1 import ToolLoop
from mu.l3 import Orchestrator
from tools import TOOLS

utf8_console()

DEFAULT_MODEL = "gemma4:12b"  # 参照モデル（他は qwen3.5:9b）
MAX_ROUNDS = 8   # L3 の上限（呼び出し側が規定）
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限

# このタワーは L3 が最外なので、インデントは L3 起点（層ラベルは CLI の表示の持ち物）。
_L3 = "  [L3]"
_L2 = "    [L2]"
_L1 = "      [L1]"
_TOOL = "        [tool]"


def _show_units(units: list) -> None:
    if not units:
        print("  (単位なし)")
    for i, u in enumerate(units, 1):
        mark = "x" if u.get("done") else " "
        print(f"  {i}. [{mark}] {u.get('file')}")
        print(f"        task: {short(u.get('task'))}")
        print(f"        基準: {short(u.get('criterion'))}")
        check = u.get("check") or {}
        if check.get("run"):
            expect = f" → 「{short(check.get('expect'), 60)}」" if check.get("expect") else ""
            print(f"        検査: {short(check.get('run'), 80)}{expect}")


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
            raise Abort()
        if cmd == "y":
            return units
        if cmd == "n":
            raise Abort()
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
    """自律部（D・C）の進行を表示。plan/replan は _approve が対話表示するので出さない。

    共通の log（chat_common）は plan/replan を「自律承認」として表示する L4/L5 タワー用。
    この CLI は承認が対話なので、独自の subset を持つ（表示は呼び出し側の持ち物）。
    """
    kind = event[0]
    if kind == "unit_done":
        print(f"  [x] UNIT DONE  : {event[1].get('file')}")
    elif kind == "unit_failed":
        analysis = event[2]
        print(f"  [!] UNIT FAILED: {event[1].get('file')} -> {short(analysis.get('reason'))}")
        if analysis.get("suggestion"):
            print(f"      suggestion : {short(analysis.get('suggestion'))}")
    elif kind == "unit_check_failed":
        print(f"  [!] UNIT CHECK NG: {event[1].get('file')} -> {short(event[2], 140)}")
    elif kind == "unit_check_skipped":
        print(f"  [?] UNIT CHECK SKIP: {event[1].get('file')} ({short(event[2], 80)})")
    elif kind == "overall":
        # 機械的照合の結果（全単位 done か）。LLM の推測判定ではない。
        v = event[1]
        print(f"  [=] OVERALL: passed={v.get('passed')} :: {short(v.get('reason'), 160)}")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    l0 = OllamaInterface()
    # 層ごとにラベルの違う実況プロキシを合成点へ差し込む（層自体は無変更）。
    # Agent の l0 は Reflect 専用、Orchestrator の l0 は Plan/分析/全体判定専用
    # なので、ラベル＝呼び出し元の層が正確に対応する。
    l1 = ToolLoop(VerboseL0(l0, _L1))
    l2 = Agent(VerboseL0(l0, _L2), l1)
    orch = Orchestrator(VerboseL0(l0, _L3), l2)
    tools = verbose_tools(TOOLS, _TOOL)

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
                model, goal, tools,
                approve=_approve, log=_log, system=env_preamble(),
                max_rounds=MAX_ROUNDS, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except Abort:
            print("— 中断しました")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        status = "完遂 ✓" if result["done"] else f"未達 ✗（{result.get('rounds')}周で上限到達）"
        print(f"=== {status} ===")
        for u in result["units"]:
            print(f"  {'[x]' if u.get('done') else '[ ]'} {u.get('file')}")


if __name__ == "__main__":
    main()
