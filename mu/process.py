"""プロセス（役割注釈付きタスク列）とその artifact — 層の外にある facility。

L4（進行の層）が扱うデータ型と、その入出力をここに置く。**判断はしない**——
何を再実行するかを決めるのは PjM（LLM）であり、ここにあるのは決められた通りに
状態を動かす決定論だけ（合意009）。

    task = {role, task, file, criterion, check?, model?, done}

この層の床（コードが必ず守る不変条件）:
  - 末尾に QA タスクが無ければ**必ず足す**（検証を飛ばして完遂に到達できない）。
    文面・出力ファイル・成功条件は役割定義書で上書きできるが、**存在は上書きできない**
  - 判定書の契約（ACHIEVED / REASON / GAP）を供給し、QA タスクの成功条件にも入れる
  - 無効化はファイル依存で伝播し、**QA タスクは必ず再実行**（done を carry しない）
  - 判定書の読み手は装飾に寛容だが、**判定語 yes|no|uncertain は厳格**（曖昧な宣言は読めない扱い）

依存グラフ（`invalidate` が使うファイル依存）は**並列可能性を判定するグラフと同一物**であり、
並列実行を入れるときに触るのもここ（合意006）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .role_kb import role_section

_DEFAULT_QA_TASK = {
    "role": "qa",
    "task": "受け入れ基準に照らして成果物を独立に検証し、判定書を書く",
    "file": "verdict.md",
    "criterion": "受入基準の番号ごとに『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を1行ずつ書く",
}

# 019: 「FAIL を含む判定書も完成」を成功条件に明記する。L2 Reflect はこの criterion に
# 対して合否を判定するため、これが無いと「ITEM n: FAIL がある＝仕事が終わっていない」と
# 誤読し、QA に成果物の修正を要求し続ける（018 実走。「判定を直しに行く」圧力）。
_VERDICT_REQUIREMENT = (
    "判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。"
    "**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**"
    "（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）"
)

_VERDICT_CONTRACT = (
    "判定書の書式（機械的に読まれる。厳守）:\n"
    "SPEC.md の受入基準を**番号順に1つずつ**判定し、**すべての番号について**1行ずつ書くこと。\n"
    "ITEM <番号>: PASS|FAIL|UNCERTAIN — <根拠。成果物からの引用、または実行した検査と出力>\n"
    "GAP: <PASS でない項目について、何が欠けているか>\n"
    "\n"
    "規律:\n"
    "- **総合判定は書かない。** 全体として合格かどうかを決めるのはあなたではなくコードである。\n"
    "  あなたの仕事は1項目ずつの二値判定と、その根拠を挙げることだけ。\n"
    "- **根拠のない PASS を書かない。** 成果物のどこを見たかを引用する。引用できないなら PASS ではない。\n"
    "- 判定できない項目は UNCERTAIN と書く（推測で PASS にしない）。UNCERTAIN は未達として扱われる。\n"
    "- 飛ばした番号は UNCERTAIN とみなされる。書かなければ通る、ということはない。\n"
    "- **不合格は不合格と書いて完成である。** FAIL を書いた判定書は失敗ではない——それが検証の\n"
    "  成果である。FAIL を消すために成果物を直そうとしたり、判定を甘くしたりしてはならない。\n"
    "  成果物の修正は、あなたの判定書を受け取った進行側が別のタスクとして回す。"
)

# 判定書の項目行。契約はコードが供給するが書き手は LLM なので、装飾（**・箇条書き・全角）は許容し、
# 判定語だけを厳格に読む（verdict.md の従来の読み方と同じ作法）。
_ITEM_LINE = re.compile(
    r"(?im)^\W*item\s*(\d+)\s*[:：]\s*\**\s*(pass|fail|uncertain)\b\**\s*[—\-–:：]?\s*(.*)$"
)

_PROCESS_NOTE = "（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）"


def verdict_check(file: str) -> dict:
    """判定書 unit に付ける正準検査（コード供給）。

    019p4 実走: L3 が判定書の unit に自作の検査を発明し、その検査自体が壊れて
    （実在しないコマンドレット・ParserError・ありえない expect）正しい判定書を3回落とした。
    判定書の中身はコード（read_verdict）が読む——unit の検査は「規定の形式で存在するか」を
    見る最小のものでよく、LLM に発明させない（合意008 の貫徹）。
    """
    return {"run": f'Get-Content "{file}"', "expect": "ITEM 1:"}


def task_contract(task: dict) -> str:
    """タスクに紐づくポジションの契約（コード供給）。いまは QA の判定書契約だけ。

    019 実走で判明: 契約を task_goal にだけ載せると、L3 が unit を計画し直すたびに
    **転記から欠落**して L2 に届かない（規範が確率的な転記に乗る）。呼び出し側（L4）は
    これを task の system に載せる——system は L3→L2 へコードが素通しで運ぶため、
    再計画で薄まらない。goal 側の記載も残す（計画者にも見せる。二重化であって重複ではない）。
    """
    return _VERDICT_CONTRACT if task.get("role") == "qa" else ""


def default_qa_task(roles: dict) -> dict:
    """コードのミニマム定義に、役割定義書の宣言を重ねた QA タスクを作る（合意008）。"""
    doc = roles.get("qa") if isinstance(roles.get("qa"), dict) else {}
    task = dict(_DEFAULT_QA_TASK)
    for key in ("task", "file", "criterion"):
        value = str((doc or {}).get(key, "") or "").strip()
        if value:
            task[key] = value
    return task


def process_note(roles: dict) -> str:
    """PROCESS.md の注記。定義書の `## process-artifact` があればそれ、無ければミニマム。"""
    return role_section(roles.get("pjm"), "process-artifact") or _PROCESS_NOTE


def normalize_tasks(raw: list, roles: dict, log: Callable) -> list:
    """PjM 応答をタスク列に正規化する。末尾に QA タスクが無ければコードが必ず足す。"""
    tasks = []
    for t in raw:
        if not isinstance(t, dict):
            continue
        file = str(t.get("file", "")).strip()
        text = str(t.get("task", "")).strip()
        if not file or not text:
            continue
        role = str(t.get("role", "")).strip()
        if roles and role not in roles:
            log(("role_fallback", role, "implementer"))
            role = "implementer"
        task = {
            "role": role, "task": text, "file": file,
            "criterion": str(t.get("criterion", "")), "done": False,
        }
        check = t.get("check") or {}
        if isinstance(check, dict) and (check.get("run") or "").strip():
            task["check"] = {"run": str(check["run"]), "expect": str(check.get("expect", "") or "")}
        if (t.get("model") or "").strip():
            task["model"] = str(t["model"])
        tasks.append(task)
    if not any(t["role"] == "qa" for t in tasks):
        qa = default_qa_task(roles)          # ミニマム＋定義書の宣言（存在自体は上書き不可）
        log(("qa_appended", qa["file"]))
        tasks.append(dict(qa, done=False))
    for t in tasks:                           # 判定書の契約は成功条件にも入れる（床）
        if t["role"] == "qa" and "REASON" not in t["criterion"]:
            t["criterion"] = (t["criterion"] + " / " if t["criterion"] else "") + _VERDICT_REQUIREMENT
    return tasks


def task_goal(task: dict, spec_path: str, prior_files: list, purpose: str = "") -> str:
    goal = (
        f"{task['task']}\n"
        f"役割: {task['role']}\n"
        f"出力ファイル: {task['file']}\n"
        f"成功条件（これを満たすこと）: {task['criterion']}"
    )
    check = task.get("check") or {}
    if check.get("run"):
        goal += f"\n検証コマンド（コード側で実行される）: {check['run']}"
        if check.get("expect"):
            goal += f"\n検証コマンドの出力に必ず含めるべき文字列: {check['expect']}"
    if task.get("last_failure"):
        # 理由を添えずに再実行させると、実行者は成果物でなく**検査器の方**を直しにいく
        # （013 実走で観測）。載せるのはコードが実行した事実だけ（合意014 ①）。
        goal += (
            f"\n\n前回の失敗（コードが実行した事実。あなたの前回の試みはこれで落ちた）:\n"
            f"{task['last_failure']}\n"
            "※ 直すのは**成果物の側**である。検査コマンドや検査スクリプトを書き換えて"
            "通そうとしてはならない。"
        )
    refs = [spec_path, *prior_files]
    goal += f"\n参照できるファイル（read_file で読む）: {', '.join(refs)}"
    if task["role"] == "qa":
        goal += f"\n\n{_VERDICT_CONTRACT}"       # 契約はコードが供給する（合意008）
    if task["role"] == "qa" and purpose:
        # QA だけは目的の原文も見る（合意007 C1-(b)）。SPEC は PdM の生成物であり、
        # 目的の制約を弱めた仕様が下りてくる経路（H3）が実在する。仕様に忠実であることと
        # 目的が達成されたことは別であり、その差を検査できるのは原文を持つ QA だけ。
        goal += (
            f"\n\n目的の原文（PURPOSE。人間が言った言葉。SPEC はこれを PdM が仕様化したもの）:\n{purpose}\n"
            "※ 受入基準の検査に加えて、SPEC が上の目的の制約を弱めていないか"
            "（制約を落とす・言い換えて緩める・退化解を許す）も検査すること。"
            "弱めていれば、その受入基準を FAIL とし、GAP にその矛盾を書く。"
        )
    return goal


def invalidate(tasks: list, files: list, failure: str = "") -> None:
    """指定ファイルのタスクを無効化し、依存（**後続**タスクの記述に現れるファイル）へ伝播する。

    QA タスクは必ず無効化する（部分再実行の経路から「検証を飛ばして完遂」に到達させない）。
    判断（どこを無効化するか）は PjM、伝播はここ（コードの決定論）。

    伝播は**後続方向だけ**（合意014 B）。言及だけを根拠にすると依存が逆流する——013 の実走で、
    検査器タスク（前段）が成果物名に言及していたために巻き込まれ、**PjM が凍結を守る判断を
    していたのにコードが検査器を再生成させた**。プロセスは依存順に並ぶ契約（PjM プロンプト
    「依存が先に来るよう並べよ」）なので、**前段は後段に依存しない**。これが限定の根拠。

    `failure` を渡すと、無効化したタスクに「前回の失敗（コードが実行した事実）」として載せる。
    実行者は理由を知らされないと成果物でなく検査器を直しにいく（013 の実害・合意014 A）。
    """
    invalid = {str(f).strip() for f in files if str(f).strip()}
    producer = {t["file"]: i for i, t in enumerate(tasks)}   # そのファイルを産むタスクの位置
    touched = set()
    changed = True
    while changed:  # 固定点まで伝播（invalid 集合は単調増加なので停止する）
        changed = False
        for idx, t in enumerate(tasks):
            if t["file"] in invalid:
                if t.get("done"):
                    t["done"] = False
                    changed = True
                touched.add(idx)
                continue
            texts = " ".join([
                t.get("task", ""), t.get("criterion", ""),
                (t.get("check") or {}).get("run", ""), (t.get("check") or {}).get("expect", ""),
            ])
            # 言及＝依存とみなすのは、そのファイルを産むタスクが**自分より前**にいるときだけ。
            # 産出タスクがタスク列に無いファイル（外部入力等）は保守的に依存とみなす。
            if any(f in texts and producer.get(f, -1) < idx for f in invalid):
                invalid.add(t["file"])
                t["done"] = False
                touched.add(idx)
                changed = True
    if failure:
        for idx in touched:
            tasks[idx]["last_failure"] = failure
    for t in tasks:
        if t["role"] == "qa":
            t["done"] = False


def clear_failure(task: dict) -> None:
    """タスクが通ったら前回の失敗を捨てる（持つのは直近1回だけ。合意014 ②）。"""
    task.pop("last_failure", None)


def carry_done_tasks(old: list, new: list) -> list:
    """replan 後の done 引き継ぎ。file が両側で一意な非 QA タスクのみ（_carry_done と同じ防御）。

    QA タスクは決して carry しない — 再計画後は必ず検証し直す。
    """
    from collections import Counter
    old_c = Counter(t["file"] for t in old)
    new_c = Counter(t["file"] for t in new)
    done_files = {
        t["file"] for t in old
        if t.get("done") and t["role"] != "qa" and old_c[t["file"]] == 1 and new_c[t["file"]] <= 1
    }
    for t in new:
        if t["role"] != "qa" and t["file"] in done_files:
            t["done"] = True
    return new


def summarize(tasks: list) -> str:
    return "\n".join(
        f"- [{'x' if t.get('done') else ' '}] ({t['role']}) {t['file']}: {t['task']}"
        for t in tasks
    )


def read_verdict(tasks: list, criteria: list) -> dict | None:
    """最後の QA タスクの判定書を**項目ごとに**読み、**コードが集約する**（合意017）。

    完成 = 受入基準の**全項目が PASS**。部分達成を完成と呼ばない。
    総合判定は LLM から取り上げている——「全体としてどうか」を問うと寛容側に倒れるため
    （012 では決定論 check が 3件中2件 NG なのに QA は yes と書いた）。
    LLM が担うのは1項目ずつの二値判定と根拠だけで、集約はここで行う。

    QA 未完なら None。判定書が無い・読めないは uncertain（安全側）。
    判定書に現れない受入基準は uncertain として並べる——黙って落とすと
    「書かなければ通る」抜け道になる。
    """
    qa = [t for t in tasks if t["role"] == "qa"]
    if not qa or not qa[-1].get("done"):
        return None
    p = Path(qa[-1]["file"])
    if not p.is_file():
        return {
            "achieved": "uncertain", "reason": f"verdict file missing: {qa[-1]['file']}",
            "gap": "", "items": [],
        }
    text = p.read_text(encoding="utf-8", errors="replace")
    found = {}
    for num, verdict, evidence in _ITEM_LINE.findall(text):
        found[int(num)] = (verdict.lower(), evidence.strip())
    items = []
    for i, c in enumerate(criteria or [], 1):
        verdict, evidence = found.get(i, ("uncertain", "判定書に項目が無い"))
        items.append({"n": i, "text": c.get("text", ""), "verdict": verdict, "evidence": evidence})
    return {**_summarize_items(items), "gap": _verdict_field(text, "GAP"), "items": items}


def _summarize_items(items: list) -> dict:
    """項目の二値を集約する（コードの決定論。ここに LLM の判断は入らない）。"""
    if not items:
        return {"achieved": "uncertain", "reason": "受入基準が無く、判定する対象がない"}
    failed = [i for i in items if i["verdict"] == "fail"]
    unknown = [i for i in items if i["verdict"] == "uncertain"]
    if not failed and not unknown:
        return {"achieved": "yes", "reason": f"受入基準 {len(items)} 項目すべて PASS"}
    parts = []
    if failed:
        parts.append("未達 " + ", ".join(f"#{i['n']} {i['text']}" for i in failed))
    if unknown:
        parts.append("判定不能 " + ", ".join(f"#{i['n']} {i['text']}" for i in unknown))
    return {
        # どちらも「達成ではない」。ただし **FAIL（未達と分かった）と UNCERTAIN（判定できなかった）**は
        # 上位の判断が変わる——前者は作り直し、後者は仕様か検証方法を疑う。値でも区別する。
        "achieved": "no" if failed else "uncertain",
        "reason": f"{len(items)} 項目中 PASS は {len(items) - len(failed) - len(unknown)}（"
                  + " / ".join(parts) + "）",
    }


def _verdict_field(text: str, name: str, limit: int = 600) -> str:
    """判定書の REASON / GAP を読む。1行形式でも Markdown 見出しブロックでも拾う。

    契約はコードが供給するが、書き手は LLM であり装飾（`## REASON` ＋本文）へ流れる
    （008 Phase4 の実走で観測）。**判定語 yes|no|uncertain の厳格さは保ったまま**、
    根拠の文面だけは実体に合わせて頑健に読む——読めないと人間に渡る情報が消えるため。
    """
    inline = re.search(rf"^\W{{0,4}}{name}\s*:\s*(\S.*)$", text, re.M | re.I)
    if inline:
        return inline.group(1).strip()[:limit]
    block = re.search(rf"^#+\s*{name}\s*:?\s*$\n(.+?)(?=^#|\Z)", text, re.M | re.S | re.I)
    if block:
        body = " ".join(line for line in block.group(1).split() if line)
        return body[:limit]
    return ""


def write_process(process_path: str, purpose: str, tasks: list, note: str = "") -> None:
    """プロセス（体制表）を artifact に書く。誰が・どの役割で・どのモデルで・何を作るか。"""
    lines = []
    for i, t in enumerate(tasks, 1):
        mark = "x" if t.get("done") else " "
        model = f"（model: {t['model']}）" if t.get("model") else ""
        lines.append(f"{i}. [{mark}] **{t['role']}**{model} → `{t['file']}`")
        lines.append(f"   - task: {t['task']}")
        lines.append(f"   - 成功条件: {t.get('criterion', '')}")
        check = t.get("check") or {}
        if check.get("run"):
            expect = f" → 「{check.get('expect', '')}」" if check.get("expect") else ""
            lines.append(f"   - 検査: `{check['run']}`{expect}")
    text = (
        "# PROCESS — L4（PjM）が編んだプロセス（体制表）\n"
        f"{note or _PROCESS_NOTE}\n\n"
        f"## 目的\n{purpose}\n\n"
        f"## タスク列\n" + "\n".join(lines) + "\n"
    )
    p = Path(process_path)
    if p.parent != Path("."):
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
