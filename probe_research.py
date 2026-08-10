r"""probe_research.py — 非コーディング領域（ディープリサーチ）で mu の層構造を検証する probe。

合意012。**成果物の出来は主目的ではない**。コーディング用に育てた層構造
（L5 目的→仕様 / L4 プロセス・人選 / 役割 / 独立 QA / 決定論 check）が、
成果物がコードでない領域でそのまま働くか、**どこで噛み合わないか**を観測する。

case:
  link   — L2 単走。モデルが web_search → fetch_url → write_file を**繋げられるか**だけ見る
           （011 の未検証点。ここが通らなければ L5 実走は層の検証にならない）
  runtime— L5 実走。ローカル LLM 実行基盤の比較レポートを、目的だけ渡して書かせる

使い方:
    .\.venv\Scripts\python.exe probe_research.py <case> <model> <workdir> [qa_model]
既定の想定: model=gemma4:31b-cloud / qa_model=qwen3.5:9b（QA は別ファミリー＝非相関）
"""

import os
import sys
import time
from pathlib import Path

import tools as tools_mod
from chat_common import (
    ROLES_DIR, VerboseL0, env_preamble, log, verbose_tools,
    L5 as _L5, L4 as _L4, L3 as _L3, L2 as _L2, L1 as _L1,
)
from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Manager
from mu.l5 import Director
from mu.role_kb import load_roles
from tools import TOOLS

L5_MAX = 2
L4_MAX = 3
L3_MAX = 8
L2_MAX = 6
L2_L1_MAX = 12   # 検索→取得→書き出しは周が要る（コーディングより 1 タスクの工程が多い）

# 壁時計の予算（秒）。外部 kill は finally を飛ばし観測ゼロを生む——内部締切で終わらせる（合意018 ⑥）。
TIME_BUDGET = int(os.environ.get("MU_TIME_BUDGET", "1500"))

# --- link: L2 単走。web ツールを繋げられるかだけを見る最小の課題 ---
_LINK_GOAL = (
    "Ollama の structured outputs（構造化出力）について、公式ドキュメントを web で調べ、"
    "分かったことを findings.md に日本語で書け。findings.md には必ず "
    "(1) 参照した公式ドキュメントの URL、(2) 要点を3つ、を含めること。"
    "推測で書かず、必ず web_search と fetch_url で実際のページを読んでから書くこと。"
)

# --- runtime: L5 実走。目的（なぜ）だけを渡し、仕様化は PdM に委ねる ---
_RUNTIME_PURPOSE = (
    "ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、"
    "mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを"
    "判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、"
    "主張には必ず出典 URL を添えること。"
)


def _run_link(model: str, workdir: Path) -> dict:
    """L2 単走: web_search → fetch_url → write_file が繋がるか。"""
    l0 = OllamaInterface()
    agent = Agent(VerboseL0(l0, _L2), ToolLoop(VerboseL0(l0, _L1)))
    tools = verbose_tools(TOOLS)
    messages: list = [
        {"role": "system", "content": env_preamble()},
        {"role": "user", "content": _LINK_GOAL},
    ]
    used: list = []
    passed = False
    for r in range(1, L2_MAX + 1):
        mark = len(messages)
        messages, verdict = agent.step(model, messages, _LINK_GOAL, tools, l1_max=L2_L1_MAX)
        for m in messages[mark:]:
            if m.get("role") == "tool":
                used.append({"tool": m["tool_name"], "ok": m.get("ok"), "facts": m.get("facts", {})})
        print(f"[reflect {r}] passed={verdict['passed']} :: {verdict['reason'][:160]}", flush=True)
        if verdict["passed"]:
            passed = True
            break
    out = workdir / "findings.md"
    return {
        "passed": passed,
        "tools_used": [u["tool"] for u in used],
        "web_calls": [u for u in used if u["tool"] in ("web_search", "fetch_url")],
        "artifact_exists": out.exists(),
        "artifact_bytes": out.stat().st_size if out.exists() else 0,
    }


def _run_runtime(model: str, qa_model: str, workdir: Path) -> dict:
    """L5 実走: 目的だけ渡す。仕様・プロセス・人選・QA はすべて mu が決める。"""
    l0 = OllamaInterface()
    l1 = ToolLoop(VerboseL0(l0, _L1))
    l2 = Agent(VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(VerboseL0(l0, _L3), l2)
    l4 = Manager(VerboseL0(l0, _L4), l3)
    director = Director(VerboseL0(l0, _L5), l4)
    roles = load_roles(ROLES_DIR)
    # judge（LLM 検査器）は実行体とモデルの注入が要るので、ここで組んで渡す（環境接地は caller の責務）。
    # 判定者は QA と同じモデルでよい——別モデルが使える環境かは環境依存であり、前提にしない。
    # 独立性を作っているのはモデル差ではなく**文脈非共有**の方である（合意015）。
    judge_tool = (tools_mod.make_judge(l0, qa_model), tools_mod.JUDGE_USAGE)
    t0 = time.monotonic()
    return director.run(
        model, _RUNTIME_PURPOSE, verbose_tools([*TOOLS, judge_tool]),
        roles=roles, models=[model, qa_model],
        log=log, system=env_preamble(),
        guard=tools_mod.protection_violations,   # 守られるべき入力の破れで即停止（合意016→018）
        deadline=lambda: time.monotonic() - t0 > TIME_BUDGET,   # 内部締切（合意018 ⑥）
        max_rounds=L5_MAX, l4_max=L4_MAX, l3_max=L3_MAX,
        l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
    )


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    case, model, workdir = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve()
    qa_model = sys.argv[4] if len(sys.argv) > 4 else "qwen3.5:9b"
    workdir.mkdir(parents=True, exist_ok=True)
    os.chdir(workdir)  # file grounding は cwd（使い捨てディレクトリで走らせる）

    # probe 自身の出力は print で出す。`log`（chat_common）は L5 側のイベントタプル用であり、
    # 文字列を渡すと event[0] が先頭 1 文字になって**どの分岐にも当たらず黙って捨てられる**
    # （初回走行で最終結果の記録を落とした。silent-degradation の実例）。
    print(f"=== probe_research {case} / model={model} qa={qa_model} / {workdir} ===", flush=True)
    started = time.time()
    try:
        if case == "link":
            result = _run_link(model, workdir)
        elif case == "runtime":
            result = _run_runtime(model, qa_model, workdir)
        else:
            print(f"unknown case: {case}")
            sys.exit(2)
    except L0Error as e:
        print(f"[L0Error] {e}", flush=True)
        raise
    finally:
        # 破れの記録は**解除の前に**取る（解除後は登録が消えて検出できない。probe_hard と同じ順序）。
        violations = tools_mod.protection_violations()
        tools_mod.clear_protection()   # OS レベルの保護を必ず外す（合意016 ①）
    elapsed = time.time() - started

    print(f"=== RESULT ({case}) in {elapsed:.0f}s ===", flush=True)
    for key, value in result.items():
        if key == "tasks":
            for t in value:
                print(f"  {'[x]' if t.get('done') else '[ ]'} ({t['role']}) {t.get('file')}")
            continue
        print(f"  {key}: {str(value)[:400]}")
    print(f"  protection violations: {violations if violations else 'none'}", flush=True)


if __name__ == "__main__":
    main()
