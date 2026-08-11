r"""l4_chat.py — L4（進行の層 / PjM）を単体で触る最小 CLI。

L5（目的の層）を通さず、**仕様（SPEC）を直接渡して**進行の層だけを動かす。
PjM がプロセスを編み、役割を着せた L3 が1タスクずつ完遂し、決定論 check と
独立 QA の verdict が集まる——その結果として返る `outcome` が観測対象:

    done     … 受入基準・verdict とも通った
    respec   … 仕様が悪いと PjM が判断した（この層では直せない。L5 の仕事）
    escalate … 人手が要る／PjM の予算が尽きた

使い方:
    .\.venv\Scripts\python.exe l4_chat.py <spec.json|spec.md> [model] [追加モデル...]

- `.json` は L5 が作る仕様の形（`{definitions, criteria, spec}`）をそのまま受ける。
  `criteria` の各要素に `run` / `expect` があれば決定論 check として実行される。
- `.md` / `.txt` は本文をそのまま仕様として扱う（受入基準なし＝verdict だけで判定）。

成果物・PROCESS.md・verdict.md は cwd に生成される。使い捨てのディレクトリで実行すること。
"""

import json
import sys
from pathlib import Path

from chat_common import (
    VerboseL0, env_preamble, log, roles_paths, short, show_roles, utf8_console, verbose_tools,
    L4 as _L4, L3 as _L3, L2 as _L2, L1 as _L1,
)
from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Manager
from mu.role_kb import load_roles
from tools import TOOLS

utf8_console()

DEFAULT_MODEL = "gemma4:12b"
L4_MAX = 3       # PjM 判断サイクル（rerun/replan の回数）。上限は呼び出し側が規定する
L3_MAX = 8
L2_MAX = 6
L2_L1_MAX = 10


def _load_spec(path: Path) -> dict:
    """仕様を読む。JSON は L5 の形をそのまま、それ以外は本文を仕様として扱う。"""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        return {
            "definitions": data.get("definitions", []),
            "criteria": data.get("criteria", []),
            "spec": str(data.get("spec", "")),
            "feasible": True, "conflicts": [],
        }
    return {"definitions": [], "criteria": [], "spec": text, "feasible": True, "conflicts": []}


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    spec_file = Path(sys.argv[1]).resolve()
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    pool = [model, *sys.argv[3:]]
    roles = load_roles(*roles_paths())   # 切替は MU_ROLES_DIR（合意026）
    spec = _load_spec(spec_file)

    l0 = OllamaInterface()
    l3 = Orchestrator(VerboseL0(l0, _L3), Agent(VerboseL0(l0, _L2), ToolLoop(VerboseL0(l0, _L1))))
    manager = Manager(VerboseL0(l0, _L4), l3)

    print(f"L4 chat / model={model}  pool={pool}  l4_max={L4_MAX}")
    show_roles(roles, roles_paths())
    print(f"spec: {spec_file}")
    print(f"  {short(spec['spec'], 200)}")
    try:
        outcome = manager.run(
            model, spec, verbose_tools(TOOLS),
            roles=roles, models=pool, log=log, system=env_preamble(),
            max_rounds=L4_MAX, l3_max=L3_MAX, l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
        )
    except L0Error as e:
        print(f"[L0:{type(e).__name__}] {e}")
        sys.exit(2)

    print("=== OUTCOME ===")
    print(f"outcome: {outcome['outcome']}  (ok={outcome['ok']}, rounds={outcome['rounds']})")
    if outcome["reason"]:
        print(f"reason : {short(outcome['reason'], 300)}")
    for t in outcome["tasks"]:
        model_s = f" @{t['model']}" if t.get("model") else ""
        print(f"  {'[x]' if t.get('done') else '[ ]'} ({t['role']}{model_s}) {t.get('file')}")
    verdict = outcome["verdict"]
    if verdict:
        print(f"verdict: {verdict['achieved']} :: {short(verdict.get('reason'), 200)}")
    for c in outcome["checks"]:
        mark = "ok" if c.get("ok") else ("skip" if c.get("ok") is None else "NG")
        print(f"check[{mark}] {short(c.get('text'), 80)}")


if __name__ == "__main__":
    main()
