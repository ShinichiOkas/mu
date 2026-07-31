r"""probe_l4.py — L4（Director）の受入検証を非対話で実走する probe。

review は既定の自動レビュー（L4 の判定が yes のときだけ受理）。したがって
uncertain / no は escalated=True で終わる — 合意005 の受入条件
「黙って 完遂 ✓ を返さない（検出されるか、人間に上がる）」をそのまま検証する。

題材:
  f1    : F1（todo_app.py 1ファイル縛りの TODO アプリ）。偽・完遂を観測した実走の再現
  sales : データ→答え型（売上表から不採算商品の特定）。定義の artifact 化を観測する

使い方:
    .\.venv\Scripts\python.exe probe_l4.py <f1|sales> <model> <workdir> [qa_model]
workdir は使い捨てディレクトリを指定する（成果物・SPEC.md・PROCESS.md がそこに作られる）。
qa_model を渡すと PjM の人選プールに加わる（QA を別ファミリーに出す等）。
"""

import json
import os
import sys
import time
from pathlib import Path

from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Director, load_roles
from tools import TOOLS
from l4_chat import _VerboseL0, _verbose_tools, _log, _env_preamble, _L4, _L3, _L2, _L1, ROLES_DIR

L4_MAX = 2      # probe は自動レビューなので改訂ループは1回まで（実行時間の抑制）
L3_MAX = 8
L2_MAX = 6
L2_L1_MAX = 10

PURPOSES = {
    # F1 原文（docs/experiment-2026-07-20-f1.md）。偽・完遂を2走とも出した題材。
    "f1": (
        "todo_app.py 1ファイルだけでCLIのTODO管理アプリを作る。機能: 追加・削除・一覧・完了・"
        "期限(YYYY-MM-DD)・優先度・キーワード検索・undo・JSON自動保存。成功条件: "
        "python todo_app.py --selftest が全機能を検査して exit 0（セルフテスト12件以上）。"
        "todo_app.py 以外のファイルを作らないこと。"
    ),
    # データ→答え型（合意005 の完了条件の題材。師匠の例をそのまま使う）。
    "sales": "この売上表 sales.csv から不採算商品を特定してくれ。",
}

# sales.csv: 粗利率 = (販売価格-原価)/販売価格。5% 未満は SD カード(2.4%)・乾電池(4.8%)・
# コピー用紙(0%)・USB ケーブル(-6.7%) の4品。3%未満なら SD カード・コピー用紙・USB ケーブルの3品。
SALES_CSV = """商品,販売価格,原価,販売数
ノートPC,120000,96000,34
モニター,32000,27200,58
キーボード,8500,5950,210
マウス,4200,3150,340
USBケーブル,600,640,820
SDカード,2500,2440,150
乾電池,420,400,960
コピー用紙,500,500,480
デスクライト,6800,4760,95
ヘッドセット,9800,7350,120
ウェブカメラ,7600,6460,80
ドッキングステーション,18000,16200,45
"""


def main() -> None:
    case, model, workdir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    pool = [model, *sys.argv[4:]]
    purpose = PURPOSES[case]
    roles = load_roles(ROLES_DIR)  # chdir 前に repo の roles/ を読む
    workdir.mkdir(parents=True, exist_ok=True)
    os.chdir(workdir)
    if case == "sales":
        Path("sales.csv").write_text(SALES_CSV, encoding="utf-8")

    l0 = OllamaInterface()
    l1 = ToolLoop(_VerboseL0(l0, _L1))
    l2 = Agent(_VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(_VerboseL0(l0, _L3), l2)
    director = Director(_VerboseL0(l0, _L4), l3)

    print(f"probe_l4 case={case} model={model} pool={pool} roles={sorted(roles)} workdir={workdir}")
    print(f"purpose: {purpose}")
    t0 = time.monotonic()
    try:
        result = director.run(
            model, purpose, _verbose_tools(TOOLS),
            roles=roles, models=pool,
            log=_log, system=_env_preamble(),
            max_rounds=L4_MAX, l3_max=L3_MAX, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
        )
    except L0Error as e:
        print(f"[L0:{type(e).__name__}] {e}")
        sys.exit(2)
    elapsed = time.monotonic() - t0

    print("=== RESULT ===")
    print(json.dumps(
        {k: result[k] for k in ("achieved", "escalated", "assessment", "rounds")},
        ensure_ascii=False, indent=2,
    ))
    for t in result.get("tasks", []):
        model_s = f" @{t['model']}" if t.get("model") else ""
        print(f"  {'[x]' if t.get('done') else '[ ]'} ({t['role']}{model_s}) {t.get('file')}")
    print(f"elapsed: {elapsed:.0f}s")
    print("files in workdir:")
    for p in sorted(Path(".").iterdir()):
        if p.is_file():
            print(f"  {p.name} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
