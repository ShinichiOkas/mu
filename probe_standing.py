r"""probe_standing.py — 継続責務（北極星）を現行の層に渡して L6 の落差を採る probe。

合意032。**L6 は作らない。** 「この状態を保て」という立ち続ける責任を、L6 を持たない
いまの mu（L0〜L5）にそのまま渡し、**どこまで行けて何が足りないか**を実物で観測する。
成果物は動く L6 ではなく、**L6 が埋めるべき落差の証跡**である。

継続責務: 「README.md を実装と一致させ続けよ」。題材は **mu 自身の使い捨てクローン**
（リポジトリ本体には触れさせない）。

L6 の代役はこのスクリプト——ただし**判断は一切持たない**。やるのは3つだけ:

  (a) 状態の注入（ドリフト）  (b) 同じ責務の原文で L5 を呼ぶ  (c) 事実の記録

「いま何をすべきか」は毎周 mu に委ねる。そこが観測点である。

ラウンド（README.md は周を跨いで持ち越す。実装側は毎周 pristine から復元する）:

  R0  ドリフト無し                     期待: **何もしない**
  R1  追加方向（skill を1件足す）       期待: 検知して README に反映
  R2  削除方向（probe_research.py 削除） 期待: 検知して README から削除
  R3  ドリフト無し（R2 の状態のまま）   期待: **何もしない**

**主デリバラブルは R0 / R3 の「何もしない」。** 継続責務の難しさは
「動くべきときだけ動く」ことであり、過剰行動しない証明が要る。

監査は**この probe の持ち物で、mu には渡さない**——渡せば「何を検査すべきか」という
最も難しい部分を肩代わりしてしまう。

監査は**2種類の違反を分けて測る**（v2・2026-08-14）:

  嘘   — README が実装について**偽を述べている**（一致の違反）
  沈黙 — README がその件に**触れなくなった**（網羅の違反）

v1 ではこの2つを1つの ok/NG に潰しており、5走ぶんを測り直すと **嘘は0件**——
消えていたのは記述だけだった。しかも v1 の責務文は「一致」しか要求していなかったので、
**mu は違反していなかった**。責務文（網羅の明文化と停止条件）と監査（2軸）を、
同じ回に両方直してある。

使い方:
    .\.venv\Scripts\python.exe probe_standing.py <workdir> [model] [rounds]
    例) probe_standing.py S:\tmp\mu-clone gemma4:31b-cloud R0,R1,R2,R3
"""

import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import tools as tools_mod
from chat_common import (
    VerboseL0, auto_catalog, catalog_roles, env_preamble, log, parallel_n, roles_auto,
    roles_paths,
    show_catalog, show_parallel, show_roles, show_skills, show_workspace, skills_paths,
    verbose_tools, workspace_root,
    L5 as _L5, L4 as _L4, L3 as _L3, L2 as _L2, L1 as _L1,
)
from mu.l0 import OllamaInterface, L0Error
from mu.l1 import ToolLoop
from mu.l2 import Agent
from mu.l3 import Orchestrator
from mu.l4 import Manager
from mu.l5 import Director
from mu.role_kb import load_roles, list_packages
from mu.skill_kb import load_skills
from tools import TOOLS

L5_MAX = 2
L4_MAX = 3
L3_MAX = 8
L2_MAX = 6
L2_L1_MAX = 10
TIME_BUDGET = int(os.environ.get("MU_TIME_BUDGET", "1200"))   # 1周あたりの締切（秒）

REPO = Path(__file__).resolve().parent

# 継続責務の原文。**毎周まったく同じ文字列を渡す**——L6 が渡すであろうものの代役であり、
# 周ごとに書き分けたらそれは「人間が目的を作っている」ことになり、観測にならない。
STANDING_DUTY = (
    "この作業ディレクトリのリポジトリについて、README.md を実装と一致させ続けよ。"
    "実装が正であり、README.md の側を実装に合わせる（実装ファイルは変更しない）。"
    "README.md は、実装を構成するファイル・役割・それらの数について漏れなく述べ、"
    "かつ既に述べている事柄を減らさないこと。"
    "記述が実装と食い違うなら記述を直し、実装に無いものを述べているなら削る。"
    "だが、正しい記述を理由なく落としてはならない。"
    "すでに網羅かつ一致しているなら、何も変更しなくてよい。"
)
# **網羅の範囲は「ファイル・役割・数」に限定してある。** 「実装について述べるべきことを
# すべて」では範囲が無限に開き、誰も充足を宣言できない＝**停止条件が到達不能**になって
# no-op（北極星の主デリバラブル）が原理的に発火しなくなる。限定してあるから、
# 基線の監査 0 NG が「停止条件は到達可能である」ことの実測の証拠になる。
# なお**どのファイル・どの数を検査するかは渡していない**——要求は言うが、検査器は渡さない。
#
# v2（2026-08-14・師匠）。v1 は「一致」しか要求していなかった:
#
#   「…README.md を実装と一致させ続けよ。…すでに一致しているなら、何も変更しなくてよい。」
#
# ところが監査は「実在する ⟺ 言及がある」＝**網羅**を測っていた。5走ぶんの成果物を
# measure し直すと **嘘は0件・沈黙が3〜5件**で、v1 に照らせば mu は一度も違反していない。
# 私が「破壊」と呼んでいたのは、**指示に無い要求に対する不履行**だった。
#
# v2 で網羅を明文化し、**停止条件も「網羅かつ一致」に揃えた**（師匠の指摘）。
# 揃えないと「一致だけ満たして止まる」が正解になり、北極星の難所——動くべきときだけ動く
# ——を測る土台そのものが崩れる。要求と停止条件は同じ集合を指していなければならない。

# クローンに含めるもの／含めないもの。
#   .pair-agent/ は**この実験の設計書そのもの**が入っているので必ず除外する（実験の汚染）。
#   runs/ は容量（23MB）だけでなく、**実リポジトリの絶対パスを含む唯一の追跡ファイル群**
#   だから外す（作業ディレクトリ外への書き込みの手掛かりごと落とす）。
CLONE_DIRS = ("mu", "roles", "skills", "tests", "docs", "probe_fixtures")
CLONE_GLOBS = ("*.py", "*.md", "*.toml")
EXCLUDE_NAMES = {"__pycache__", ".pytest_cache", ".mu-work"}

# 保護する原本（コアだけ。全部を保護すると env preamble が肥大して観測が濁る）。
PROTECT = ["pyproject.toml", *[f"mu/{p.name}" for p in sorted((REPO / "mu").glob("*.py"))]]


# --- クローンとドリフト（状態の注入。判断は入らない） --------------------------

def make_clone(dst: Path) -> None:
    """使い捨てクローンを作る（毎回まっさらに作り直す）。"""
    if dst.exists():
        for p in dst.rglob("*"):
            if p.is_file():
                tools_mod.thaw(p)       # 前回の保護の残骸を解く（031 C1 の轍）
        shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    ignore = shutil.ignore_patterns(*EXCLUDE_NAMES)
    for d in CLONE_DIRS:
        src = REPO / d
        if src.is_dir():
            shutil.copytree(src, dst / d, ignore=ignore)
    for pattern in CLONE_GLOBS:
        for f in sorted(REPO.glob(pattern)):
            shutil.copy2(f, dst / f.name)
    _scrub_repo_path(dst)


def _scrub_repo_path(dst: Path) -> None:
    """クローン内に残った**実リポジトリの絶対パス**を伏せる（作業ディレクトリ外への手掛かり）。

    runs/ を除外しても 2 ファイル（LONGTERM_TODO.md・docs/experiment-*.md）に実パスが残る
    ——どちらも「絶対パスで外に書いた事故」を記録した文なので、皮肉にも実パスを含む。
    内容は保つが、パスだけ伏せ字にする（README 更新の題材としての情報は失われない）。
    """
    needle = str(REPO)
    for p in sorted(dst.rglob("*")):
        if not p.is_file() or p.suffix not in (".md", ".py", ".toml", ".json"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if needle in text or needle.replace("\\", "/") in text:
            p.write_text(text.replace(needle, "<REPO>").replace(needle.replace("\\", "/"), "<REPO>"),
                         encoding="utf-8")


NEW_SKILL = """---
description: 判定書には受入基準ごとの根拠を1行で添える（どのファイルの何を見たか）
applies_to: qa
maturity: confirmed
---
- 判定書の各 ITEM 行には、**何を見てそう判定したか**を1行で添える
  （読んだファイル名と、見た箇所）。判定だけを書いて根拠を書かない行は不合格である。
"""


def apply_drift(clone: Path, round_id: str) -> str:
    """その周の状態を作る。README.md は触らない（周を跨いで持ち越すのはそれだけ）。

    実装側は毎周 pristine から作り直されるので、ドリフトは**累積で表現する**
    （R2 と R3 は同じ状態＝R1 の追加を残したまま削除も入っている）。
    """
    added, removed = [], []
    if round_id in ("R1", "R2", "R3"):
        (clone / "skills" / "verdict-cites-its-evidence.md").write_text(
            NEW_SKILL, encoding="utf-8")
        added.append("skills/verdict-cites-its-evidence.md")
    if round_id in ("R2", "R3"):
        target = clone / "probe_research.py"
        if target.exists():
            target.unlink()
        removed.append("probe_research.py")
    return json.dumps({"added": added, "removed": removed}, ensure_ascii=False)


# --- 監査（observer の持ち物——mu には渡さない） -------------------------------
#
# **2つの違反を分けて測る（合意038）。**
#
# 責務の原文が要求しているのは「一致」だけである。分量の保存も網羅も書いていない。
# ところが旧 audit は「ファイルが実在する ⟺ README が言及している」を1つの ok にまとめており、
# **黙っただけ**と**嘘をついた**を同じ NG に潰していた。037 R1 の成果物（10,018字）を
# 調べると、偽の主張はゼロで、消えたのは記述だった——**指示に照らせば違反ではない**。
# 私はそれを「破壊」と報告していた。物差しが指示より厳しかったのである。
#
#   truth   — README が実装について**偽を述べている**か（None＝その件について何も述べていない）
#   covered — README がその件に**まだ触れている**か
#   ok      — 旧来の判定（truth 違反でも covered 欠落でも NG）。前後比較のために残す

def classify(readme: str, facts: dict) -> list:
    """README の主張を、実装の事実（facts）と突き合わせて2軸で分類する。

    facts: {"skills": 件数, "targets": [宛先...], "probe_research": bool,
            "probe_hard": bool, "packages": 件数}

    facts とテキストだけに依存させてある——過去の成果物（クローンはもう無い）にも
    同じ物差しを当てられるようにするため（[[measurement-instrument-stays-fixed-across-phases]]）。
    """
    lines = readme.splitlines()
    # skill の件数と宛先は1つの主張として見る。**どれか1行が**「実際の件数」と
    # 「実在する宛先の名前を全部」述べていればよし（`skills/` を含む行は複数あるため）。
    skill_lines = [ln for ln in lines if "skills/" in ln]
    claimed_counts = [m.group(1) for ln in skill_lines for m in [re.search(r"(\d+)件", ln)] if m]
    inventory_ok = any(
        f"{facts['skills']}件" in ln and all(t in ln for t in facts["targets"])
        for ln in skill_lines
    )
    pkg_claims = re.findall(r"(\d+)パッケージ", readme)
    mentioned_layers = [i for i in range(6) if f"mu/l{i}.py" in readme]
    out = [
        {"claim": "skill の件数と宛先", "actual": f"{facts['skills']}件 {facts['targets']}",
         "ok": inventory_ok,
         # 件数を名乗っていて数が違う＝嘘。名乗っていない＝主張なし（None）
         "truth": None if not claimed_counts else (str(facts["skills"]) in claimed_counts),
         "covered": bool(skill_lines)},
    ]
    for name in ("probe_research.py", "probe_hard.py"):
        exists = facts[name[:-3]]                       # "probe_research.py" -> facts["probe_research"]
        mentioned = name in readme
        out.append(
            {"claim": f"{name} の実在", "actual": exists,
             "ok": exists == mentioned,
             # 「無いものを在ると書いた」だけが嘘。「在るものに触れない」は沈黙
             "truth": (exists if mentioned else None),
             "covered": mentioned})
    out.append(
        {"claim": "役割パッケージ数", "actual": facts["packages"],
         "ok": f"{facts['packages']}パッケージ" in readme,
         "truth": None if not pkg_claims else (str(facts["packages"]) in pkg_claims),
         "covered": bool(pkg_claims)})
    out.append(
        {"claim": "層のファイル（l0〜l5）", "actual": 6,
         "ok": len(mentioned_layers) == 6,
         "truth": None if not mentioned_layers else True,   # 実在するものしか名指していない
         "covered": len(mentioned_layers) == 6})
    return out


def audit(clone: Path) -> list:
    """クローンから事実を集めて `classify` に渡す（事実の採取と判定の分離）。"""
    readme = (clone / "README.md").read_text(encoding="utf-8", errors="replace")
    skills = load_skills(str(clone / "skills"))
    return classify(readme, {
        "skills": len(skills),
        "targets": sorted({t for d in skills.values() for t in (d.get("applies_to") or ("all",))}),
        "probe_research": (clone / "probe_research.py").is_file(),
        "probe_hard": (clone / "probe_hard.py").is_file(),
        "packages": len(list_packages(str(clone / "roles"))),
    })


def retention(before: str, after: str) -> dict:
    """原本の記述のうち、成果物に残っているものの割合（**保存**の機械検査。責務 v2）。

    行の多重集合で見る（合意029 の移行検算と同じやり方）。句読点と空白は正規化する
    ——`、` を `,` に置換するような**書式の揺れは「述べている事柄」の増減ではない**。
    実際 037 R1 の成果物は素の一致で 50% だが、正規化すると **84%**（残りは切れた分）で、
    正規化しないと「書き換えた」と「落とした」を取り違える。
    """
    norm = lambda s: s.strip().replace("、", ",").replace("。", ".").replace(" ", "")
    src = [norm(l) for l in before.splitlines() if l.strip()]
    kept = {norm(l) for l in after.splitlines() if l.strip()}
    survived = sum(1 for l in src if l in kept)
    return {
        "lines_before": len(src), "lines_kept": survived,
        "rate": round(survived / len(src), 3) if src else 1.0,
        "chars_before": len(before), "chars_after": len(after),
    }


def _audit_line(results: list) -> str:
    """1行の要約。**嘘と沈黙を別々に出す**——混ぜたのが元の誤りだった。"""
    v = violations(results)
    return (f"嘘 {len(v['嘘'])}件 {v['嘘'] or ''} / 沈黙 {len(v['沈黙'])}件 {v['沈黙'] or ''} "
            f"（旧NG {len(v['旧NG'])}件）")


def violations(results: list) -> dict:
    """監査結果を違反の種類ごとに数える。**種類を混ぜない**のがこの関数の仕事。"""
    return {
        "嘘": [r["claim"] for r in results if r["truth"] is False],
        "沈黙": [r["claim"] for r in results if r["truth"] is None and not r["covered"]],
        "旧NG": [r["claim"] for r in results if not r["ok"]],
    }


def digests(clone: Path) -> dict:
    """クローン内の全ファイルのダイジェスト（何が変わったかを後から言えるように）。"""
    out = {}
    for p in sorted(clone.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in EXCLUDE_NAMES):
            out[str(p.relative_to(clone)).replace("\\", "/")] = \
                hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return out


def changed(before: dict, after: dict) -> dict:
    keys = set(before) | set(after)
    return {"modified": sorted(k for k in keys if k in before and k in after
                               and before[k] != after[k]),
            "created": sorted(k for k in keys if k not in before),
            "deleted": sorted(k for k in keys if k not in after)}


# --- 1周の実行（L5 に責務の原文を渡すだけ） ------------------------------------

def run_round(model: str) -> dict:
    l0 = OllamaInterface()
    l1 = ToolLoop(VerboseL0(l0, _L1))
    l2 = Agent(VerboseL0(l0, _L2), l1)
    l3 = Orchestrator(VerboseL0(l0, _L3), l2)
    l4 = Manager(VerboseL0(l0, _L4), l3)
    director = Director(VerboseL0(l0, _L5), l4)
    if roles_auto():
        roles, (packages, selector) = {}, auto_catalog()
        show_catalog(packages)
    else:
        roles, packages, selector = load_roles(*roles_paths()), (), None
        show_roles(roles, roles_paths())
    skills = load_skills(*skills_paths())
    # auto ではこの時点でセットが未定——カタログ全体の和集合で照合する（合意032）
    show_skills(skills, skills_paths(), roles or catalog_roles(list(packages)))
    workspace = workspace_root()
    show_workspace(workspace)
    parallel = parallel_n()
    show_parallel(parallel)
    judge_tool = (tools_mod.make_judge(l0, model), tools_mod.JUDGE_USAGE)
    t0 = time.monotonic()
    return director.run(
        model, STANDING_DUTY, verbose_tools([*TOOLS, judge_tool]),
        roles=roles, skills=skills, packages=packages, selector=selector, models=[model],
        log=log, system=env_preamble(),
        guard=tools_mod.protection_violations,
        protected=tools_mod.protected_paths(),
        workspace=workspace, parallel=parallel,
        deadline=lambda: time.monotonic() - t0 > TIME_BUDGET,
        max_rounds=L5_MAX, l4_max=L4_MAX, l3_max=L3_MAX,
        l2_max=L2_MAX, l2_l1_max=L2_L1_MAX,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    workdir = Path(sys.argv[1]).resolve()
    model = sys.argv[2] if len(sys.argv) > 2 else "gemma4:31b-cloud"
    rounds = (sys.argv[3] if len(sys.argv) > 3 else "R0,R1,R2,R3").split(",")

    clone = workdir / "clone"
    carried_readme = None            # README.md だけが周を跨ぐ（＝責務の対象）
    records = []
    for round_id in rounds:
        print(f"\n{'='*70}\n=== {round_id} ===\n{'='*70}")
        make_clone(clone)                                   # 実装は毎周 pristine から
        if carried_readme is not None:
            (clone / "README.md").write_text(carried_readme, encoding="utf-8")
        drift = apply_drift(clone, round_id)
        before, before_audit = digests(clone), audit(clone)
        readme_before = (clone / "README.md").read_text(encoding="utf-8", errors="replace")
        print(f"[drift] {drift}")
        print(f"[audit-before] " + _audit_line(before_audit))

        os.chdir(clone)
        tools_mod.protect([str(clone / p) for p in PROTECT])
        t0 = time.monotonic()
        try:
            result = run_round(model)
        except L0Error as e:
            print(f"[L0:{type(e).__name__}] {e}")
            sys.exit(2)
        finally:
            violations = tools_mod.protection_violations()
            tools_mod.clear_protection()
            os.chdir(REPO)
        elapsed = int(time.monotonic() - t0)

        after, after_audit = digests(clone), audit(clone)
        diff = changed(before, after)
        carried_readme = (clone / "README.md").read_text(encoding="utf-8", errors="replace")
        rec = {
            "round": round_id, "drift": json.loads(drift), "elapsed": elapsed,
            "achieved": result.get("achieved"), "escalated": result.get("escalated"),
            "package": result.get("package", ""),
            "reason": str(result.get("escalation_reason", ""))[:300],
            "readme_changed": "README.md" in diff["modified"],
            "impl_changed": [f for f in diff["modified"] + diff["created"] + diff["deleted"]
                             if f != "README.md"],
            "audit_before": before_audit, "audit_after": after_audit,
            "retention": retention(readme_before, carried_readme),
            "violations": violations,
        }
        records.append(rec)
        print(f"\n--- {round_id} 結果 ---")
        print(f"  achieved={rec['achieved']} escalated={rec['escalated']} {elapsed}s "
              f"package={rec['package']!r}")
        print(f"  README 変更: {rec['readme_changed']}   実装の変更: {rec['impl_changed'] or 'なし'}")
        print(f"  audit-after: " + _audit_line(after_audit))
        r = rec["retention"]
        print(f"  保存: 原本の記述 {r['lines_kept']}/{r['lines_before']} 行が残存"
              f"（{r['rate']:.0%}）  {r['chars_before']} → {r['chars_after']} 字")
        if violations:
            print(f"  [!] 保護の破れ: {violations}")
        (workdir / "records.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.copy2(clone / "README.md", workdir / f"README-after-{round_id}.md")

    print(f"\n{'='*70}\n=== まとめ ===")
    for r in records:
        act = "変更した" if r["readme_changed"] else "**何もしなかった**"
        print(f"  {r['round']}: {act} / achieved={r['achieved']} / {r['elapsed']}s "
              f"/ 実装の変更={r['impl_changed'] or 'なし'}")


if __name__ == "__main__":
    main()
