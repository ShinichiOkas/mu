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
from .role_kb import role_section

_DEFAULT_QA_TASK = {
    "role": "qa",
    "task": "受け入れ基準に照らして成果物を独立に検証し、判定書を書く",
    "file": "verdict.md",
    "criterion": "判定書の1行目が『ACHIEVED: 』で始まる",
}

_VERDICT_REQUIREMENT = "判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む"

_VERDICT_CONTRACT = (
    "判定書の書式（機械的に読まれる。厳守）:\n"
    "ACHIEVED: yes|no|uncertain\n"
    "REASON: <1〜3行。確認した証拠を挙げる>\n"
    "GAP: <no のとき何が欠けているか。yes/uncertain のときは空でよい>"
)

_PROCESS_NOTE = "（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）"


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
            "弱めていれば ACHIEVED: no とし、GAP にその矛盾を書く。"
        )
    return goal


def invalidate(tasks: list, files: list) -> None:
    """指定ファイルのタスクを無効化し、依存（後続タスクの記述に現れるファイル）へ伝播する。

    QA タスクは必ず無効化する（部分再実行の経路から「検証を飛ばして完遂」に到達させない）。
    判断（どこを無効化するか）は PjM、伝播はここ（コードの決定論）。
    """
    invalid = {str(f).strip() for f in files if str(f).strip()}
    changed = True
    while changed:  # 固定点まで伝播（invalid 集合は単調増加なので停止する）
        changed = False
        for t in tasks:
            if t["file"] in invalid:
                if t.get("done"):
                    t["done"] = False
                    changed = True
                continue
            texts = " ".join([
                t.get("task", ""), t.get("criterion", ""),
                (t.get("check") or {}).get("run", ""), (t.get("check") or {}).get("expect", ""),
            ])
            if any(f in texts for f in invalid):  # 無効化されたファイルに言及＝依存とみなす
                invalid.add(t["file"])
                t["done"] = False
                changed = True
    for t in tasks:
        if t["role"] == "qa":
            t["done"] = False


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


def read_verdict(tasks: list) -> dict | None:
    """最後の QA タスクの判定書を機械的に読む。QA 未完なら None、壊れは uncertain（安全側）。"""
    qa = [t for t in tasks if t["role"] == "qa"]
    if not qa or not qa[-1].get("done"):
        return None
    p = Path(qa[-1]["file"])
    if not p.is_file():
        return {"achieved": "uncertain", "reason": f"verdict file missing: {qa[-1]['file']}", "gap": ""}
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"ACHIEVED\s*:?\s*\**\s*(yes|no|uncertain)\b", text, re.IGNORECASE)
    if not m:
        return {"achieved": "uncertain", "reason": "verdict unparseable (no ACHIEVED line)", "gap": ""}
    return {
        "achieved": m.group(1).lower(),
        "reason": _verdict_field(text, "REASON"),
        "gap": _verdict_field(text, "GAP"),
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
