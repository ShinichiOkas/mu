r"""l5_chat.py — L5（目的の層 / PdM）を触る最小 CLI。目的を1行入れると全層が動く。

L5 = 目的（なぜ作るか）を受け取り、
  PdM がまず**充足可能性**を申告し（制約が同時に満たせなければ仕様を作らず人間へ上げる）、
  可能なら**作業ディレクトリの入力の実物**に接地して操作的定義＋受入基準＋仕様（SPEC.md）を定め、
  PjM が役割注釈付きプロセス（PROCESS.md）を編んで人選し、
  1タスクずつ役割を着せた L3 に完遂させ、
  末尾の QA タスク（独立文脈。SPEC・実物・**目的の原文**を見る）が書く verdict.md を
  機械的に読んで判定する層。

役割定義書はリポジトリの roles/ から読む（`mu.role_kb`。**出所は差し替え可能**で、
同じ形の dict を返せば L4 は無変更）。定義書は PjM のナレッジベースであると同時に
**役割の権限の宣言**（frontmatter の tools / write_scope）でもあり、権限はコードが適用する
——PjM が出せるのは役割名だけなので、権限は LLM 側から書き換えられない。
**5役割（pdm / pjm / architect / implementer / qa）すべてのやり方が定義書にあり**、
コード内に生命線プロンプトは無い。定義書が欠けた役割は「知識が無い状態」で動く
（その事実は `role_doc_missing` として実況に出る）。
失敗や verdict 不合格は PjM が部分再実行（rerun/replan/respec）を判断し、
判断できないときは人間に上がる。最終判定のプロンプトで
    y      = 目的達成として受理
    f XXX  = フィードバック XXX で仕様を改訂して再実行
    n      = 終了（未達のまま引き取る）
を受ける。

上限（L5_MAX / L4_MAX / L3_MAX / L2_MAX / L2_L1_MAX）はこの呼び出し側が規定する（予算の封筒）。
成果物・SPEC.md・PROCESS.md・verdict.md は cwd に生成される（file grounding）。
使い捨てのディレクトリで実行すること。

実況・環境接地の共通部は chat_common にある（表示は CLI の責務。mu の層は無変更・無関知）。

使い方:
    .\.venv\Scripts\python.exe l5_chat.py [model] [追加モデル...]
追加モデルは PjM の人選プール（例: QA を別ファミリーに出す qwen3.5:9b）。
既定モデルは gemma4:12b。開発回転は gemma4:31b-cloud を推奨（役割別3構成）。
"""

import os
import platform
import sys

import tools as tools_mod
from chat_common import (
    Abort, VerboseL0, auto_catalog, env_preamble, log, roles_auto, roles_paths, short,
    parallel_n, show_catalog, show_parallel, show_roles, show_skills, show_workspace,
    skills_paths, utf8_console, verbose_tools, workspace_root,
    L5 as _L5, L4 as _L4, L3 as _L3, L2 as _L2, L1 as _L1,
)
from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Manager
from mu.l5 import Director
from mu.role_kb import load_roles
from mu.skill_kb import load_skills
from tools import TOOLS

utf8_console()

DEFAULT_MODEL = "gemma4:12b"
L5_MAX = 2       # L5 の上限（respec サイクル＝仕様を直して回し直す回数）
L4_MAX = 3       # L4 の上限（PjM 判断サイクル＝rerun/replan の回数）
L3_MAX = 8       # 1 タスクで L3 を回す上限
L2_MAX = 6       # 1 単位で L2 を回す上限
L2_L1_MAX = 10   # L2 の 1 周で L1 を回す上限


def _review(report: dict) -> dict:
    """HITL: 目的の達成を人間が判断する（再帰の底）。"""
    a = report.get("assessment", {})
    print("── 目的レビュー ──")
    print(f"  目的: {short(report.get('purpose'), 160)}")
    print(f"  ラウンド: {'完全 ok' if report.get('ok') else '未達あり'}")
    print(f"  QA 判定: {a.get('achieved')} :: {short(a.get('reason'), 200)}")
    if a.get("gap"):
        print(f"  gap: {short(a.get('gap'), 200)}")
    print("  プロセス:")
    for t in report.get("tasks", []):
        model = f" @{t['model']}" if t.get("model") else ""
        print(f"    {'[x]' if t.get('done') else '[ ]'} ({t['role']}{model}) {t['file']}")
    print(f"  仕様書: {report.get('spec_path')} / 体制表: {report.get('process_path')}")
    while True:
        try:
            cmd = input("目的は達成？ [y=受理 / f <指示>=改訂して再実行 / n=終了] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise Abort()
        if cmd == "y":
            return {"accept": True}
        if cmd == "n":
            raise Abort()
        if cmd.startswith("f"):
            feedback = cmd[1:].strip()
            if feedback:
                return {"accept": False, "feedback": feedback}
            print("  ? 使い方: f <指示>（例: f 閾値は3%にして）")
            continue
        print("  ? y / f <指示> / n のいずれかを入力")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    pool = [model, *sys.argv[2:]]
    # 切替は MU_ROLES_DIR（合意026）。auto＝L5 の自動選択（合意028）。
    if roles_auto():
        roles, (packages, selector) = {}, auto_catalog()
    else:
        roles, packages, selector = load_roles(*roles_paths()), (), None
    skills = load_skills(*skills_paths())   # 宛先は4ポジションで指定できるので auto と独立
    l0 = OllamaInterface()
    l1 = ToolLoop(VerboseL0(l0, _L1))
    l2 = Agent(VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(VerboseL0(l0, _L3), l2)
    l4 = Manager(VerboseL0(l0, _L4), l3)
    director = Director(VerboseL0(l0, _L5), l4)
    tools = verbose_tools(TOOLS)

    print(f"L5 chat / model={model}  pool={pool}  l5_max={L5_MAX} l4_max={L4_MAX}")
    show_catalog(packages) if roles_auto() else show_roles(roles, roles_paths())
    show_skills(skills, skills_paths(), roles)
    workspace = workspace_root()           # 切替は MU_WORKSPACE（合意030）
    show_workspace(workspace)
    parallel = parallel_n()                # 切替は MU_PARALLEL（合意031）
    show_parallel(parallel)
    print(f"  cwd={os.getcwd()}  <- 成果物・SPEC.md・PROCESS.md・verdict.md はここに作られます")
    print("  環境:", platform.system(), platform.release(), "/ execute_command=PowerShell")
    print("  (目的を入力 / /exit で終了)")
    while True:
        try:
            purpose = input("purpose> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if purpose in ("/exit", "/quit"):
            break
        if not purpose:
            continue

        try:
            result = director.run(
                model, purpose, tools,
                roles=roles, skills=skills, packages=packages, selector=selector, models=pool,
                review=_review, log=log, system=env_preamble(),
                guard=tools_mod.protection_violations,  # 守られるべき入力の破れで即停止（合意016）
                workspace=workspace, parallel=parallel,
                max_rounds=L5_MAX, l4_max=L4_MAX, l3_max=L3_MAX,
                l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
            )
        except Abort:
            print("— 終了（未達のまま引き取り）")
            continue
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            continue

        if result["achieved"]:
            status = "目的達成（人間が受理）✓"
        else:
            a = result.get("assessment", {})
            status = f"未達（{a.get('achieved')}: {short(a.get('reason'), 120)}）"
        print(f"=== {status} ===")
        print(f"  体制表: {result.get('process_path')} / L4 {result.get('rounds')}周")


if __name__ == "__main__":
    main()
