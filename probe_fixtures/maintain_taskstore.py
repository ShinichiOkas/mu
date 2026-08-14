"""タスク管理ストア。JSON ファイルを台帳として、タスクの登録・更新・集計を行う。

タスクは dict で表す:

    {"id": 1, "title": "見積を送る", "status": "pending", "due": "2026-08-20",
     "tags": ["営業"], "priority": 2, "note": ""}

- status は "pending" / "done" の2値
- due は "YYYY-MM-DD" の文字列、または None（期限なし）
- priority は 1（高）〜 5（低）の整数
"""

import csv
import json
from pathlib import Path

STATUS_PENDING = "pending"
STATUS_DONE = "done"
VALID_STATUS = (STATUS_PENDING, STATUS_DONE)
PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
CSV_COLUMNS = ("id", "title", "status", "due", "tags", "priority", "note")


class TaskError(ValueError):
    """台帳の操作が仕様に反したときに送出する。"""


def next_id(tasks):
    """次に割り当てる id を返す（既存の最大 + 1。空なら 1）。"""
    if not tasks:
        return 1
    return max(int(t["id"]) for t in tasks) + 1


def validate_task(task):
    """1件のタスクが仕様を満たすか検査する。満たさなければ TaskError。"""
    for field in ("id", "title", "status", "priority"):
        if field not in task:
            raise TaskError(f"必須項目がない: {field}")
    if not str(task["title"]).strip():
        raise TaskError("title が空である")
    if task["status"] not in VALID_STATUS:
        raise TaskError(f"status が不正: {task['status']}")
    priority = task["priority"]
    if not isinstance(priority, int) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise TaskError(f"priority が範囲外: {priority}")
    due = task.get("due")
    if due is not None and not _is_date(due):
        raise TaskError(f"due の形式が不正: {due}")
    return True


def _is_date(value):
    """'YYYY-MM-DD' の形をしているか（暦としての妥当性までは見ない）。"""
    parts = str(value).split("-")
    if len(parts) != 3:
        return False
    if [len(p) for p in parts] != [4, 2, 2]:
        return False
    return all(p.isdigit() for p in parts)


def add_task(tasks, title, due=None, tags=None, priority=DEFAULT_PRIORITY, note=""):
    """タスクを1件足して、足したタスクを返す（tasks は破壊的に更新される）。"""
    task = {
        "id": next_id(tasks),
        "title": str(title).strip(),
        "status": STATUS_PENDING,
        "due": due,
        "tags": list(tags or []),
        "priority": priority,
        "note": note,
    }
    validate_task(task)
    tasks.append(task)
    return task


def get_task(tasks, task_id):
    """id でタスクを1件取り出す。無ければ TaskError。"""
    for task in tasks:
        if int(task["id"]) == int(task_id):
            return task
    raise TaskError(f"タスクが見つからない: id={task_id}")


def update_task(tasks, task_id, **fields):
    """タスクの項目を書き換えて、書き換えたタスクを返す。id は変更できない。"""
    task = get_task(tasks, task_id)
    if "id" in fields:
        raise TaskError("id は変更できない")
    unknown = [k for k in fields if k not in task]
    if unknown:
        raise TaskError(f"不明な項目: {unknown}")
    merged = dict(task)
    merged.update(fields)
    validate_task(merged)
    task.update(fields)
    return task


def delete_task(tasks, task_id):
    """タスクを1件消す。消したタスクを返す。"""
    task = get_task(tasks, task_id)
    tasks.remove(task)
    return task


def complete_task(tasks, task_id):
    """タスクを完了にする。すでに完了なら TaskError。"""
    task = get_task(tasks, task_id)
    if task["status"] == STATUS_DONE:
        raise TaskError(f"すでに完了している: id={task_id}")
    task["status"] = STATUS_DONE
    return task


def reopen_task(tasks, task_id):
    """完了したタスクを未完了に戻す。未完了なら TaskError。"""
    task = get_task(tasks, task_id)
    if task["status"] == STATUS_PENDING:
        raise TaskError(f"完了していない: id={task_id}")
    task["status"] = STATUS_PENDING
    return task


def list_tasks(tasks, status=None, tag=None, priority_max=None):
    """条件でタスクを絞り込む（指定しない条件は無視される）。"""
    if status is not None and status not in VALID_STATUS:
        raise TaskError(f"status が不正: {status}")
    out = []
    for task in tasks:
        if status is not None and task["status"] != status:
            continue
        if tag is not None and tag not in task.get("tags", []):
            continue
        if priority_max is not None and task["priority"] > priority_max:
            continue
        out.append(task)
    return out


def search_tasks(tasks, keyword):
    """title と note を対象に部分一致で探す（大文字小文字は区別しない）。"""
    needle = str(keyword).lower()
    return [t for t in tasks
            if needle in str(t["title"]).lower() or needle in str(t.get("note", "")).lower()]


def sort_tasks(tasks, key="priority"):
    """並べ替えた新しいリストを返す（元のリストは変えない）。

    key は "priority" / "due" / "id" / "title" のいずれか。
    due で並べるとき、期限なし（None）は必ず末尾に置く。
    """
    if key == "priority":
        return sorted(tasks, key=lambda t: (t["priority"], int(t["id"])))
    if key == "due":
        return sorted(tasks, key=lambda t: (t.get("due") is None, t.get("due") or "", int(t["id"])))
    if key == "id":
        return sorted(tasks, key=lambda t: int(t["id"]))
    if key == "title":
        return sorted(tasks, key=lambda t: str(t["title"]))
    raise TaskError(f"並べ替えの基準が不正: {key}")


def tag_counts(tasks):
    """タグごとの件数を dict で返す（件数の降順・同数はタグ名の昇順で並べる）。"""
    counts = {}
    for task in tasks:
        for tag in task.get("tags", []):
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def stats(tasks):
    """台帳全体の集計を返す。"""
    pending = list_tasks(tasks, status=STATUS_PENDING)
    done = list_tasks(tasks, status=STATUS_DONE)
    priorities = [t["priority"] for t in tasks]
    return {
        "total": len(tasks),
        "pending": len(pending),
        "done": len(done),
        "tags": len(tag_counts(tasks)),
        "avg_priority": round(sum(priorities) / len(priorities), 2) if priorities else 0,
    }


def load_tasks(path):
    """JSON の台帳を読む。ファイルが無ければ空の台帳を返す。"""
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TaskError("台帳の形式が不正（配列ではない）")
    for task in data:
        validate_task(task)
    return data


def save_tasks(path, tasks):
    """台帳を JSON で書き出す。書き出した件数を返す。"""
    for task in tasks:
        validate_task(task)
    Path(path).write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(tasks)


def export_csv(tasks, path):
    """台帳を CSV で書き出す。tags は '|' 区切りの1列にまとめる。"""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        for task in tasks:
            writer.writerow([
                task["id"], task["title"], task["status"], task.get("due") or "",
                "|".join(task.get("tags", [])), task["priority"], task.get("note", ""),
            ])
    return len(tasks)


def import_csv(path):
    """CSV から台帳を読む（export_csv と往復できる形式）。"""
    tasks = []
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            task = {
                "id": int(row["id"]),
                "title": row["title"],
                "status": row["status"],
                "due": row["due"] or None,
                "tags": [t for t in row["tags"].split("|") if t],
                "priority": int(row["priority"]),
                "note": row.get("note", ""),
            }
            validate_task(task)
            tasks.append(task)
    return tasks


def format_task(task):
    """1件を1行の文字列にする。"""
    mark = "x" if task["status"] == STATUS_DONE else " "
    due = task.get("due") or "----------"
    tags = ",".join(task.get("tags", [])) or "-"
    return f"[{mark}] #{int(task['id']):<3} P{task['priority']} {due} {task['title']} ({tags})"


def format_table(tasks):
    """複数件を改行区切りの文字列にする。"""
    return "\n".join(format_task(t) for t in tasks)
