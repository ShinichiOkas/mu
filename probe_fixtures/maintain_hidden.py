"""HA maintain の隠し検査（probe の持ち物。mu には渡さない）。

作業ディレクトリで走らせ、`AUDIT <ok|NG> <claim> :: <detail>` を1行ずつ出す。

見るのは3つ:
  1. 足すよう頼んだ機能（overdue_tasks / stats の overdue）が仕様どおり動くか
  2. **既存の公開 API が1つも消えていないか**（名前と引数名。保守の本丸）
  3. 既存の振る舞いが変わっていないか（与えたテストの範囲外の抜き取り検査）
"""
import inspect
import os
import sys
import tempfile

# 元の taskstore.py が公開していたもの。1つでも欠ければ「作り直して失った」ことになる。
EXPECTED_API = {
    "next_id": ["tasks"],
    "validate_task": ["task"],
    "add_task": ["tasks", "title", "due", "tags", "priority", "note"],
    "get_task": ["tasks", "task_id"],
    "update_task": ["tasks", "task_id"],
    "delete_task": ["tasks", "task_id"],
    "complete_task": ["tasks", "task_id"],
    "reopen_task": ["tasks", "task_id"],
    "list_tasks": ["tasks", "status", "tag", "priority_max"],
    "search_tasks": ["tasks", "keyword"],
    "sort_tasks": ["tasks", "key"],
    "tag_counts": ["tasks"],
    "stats": ["tasks"],
    "load_tasks": ["path"],
    "save_tasks": ["path", "tasks"],
    "export_csv": ["tasks", "path"],
    "import_csv": ["path"],
    "format_task": ["task"],
    "format_table": ["tasks"],
}
EXPECTED_CONSTANTS = ["STATUS_PENDING", "STATUS_DONE", "VALID_STATUS", "PRIORITY_MIN",
                      "PRIORITY_MAX", "DEFAULT_PRIORITY", "CSV_COLUMNS", "TaskError"]

RESULTS = []


def check(claim, fn):
    """1つ測る。落ちても続ける——全部の欄を毎回埋めるため（物差しの固定）。"""
    try:
        RESULTS.append((True, claim, fn() or "ok"))
    except Exception as e:                       # noqa: BLE001
        RESULTS.append((False, claim, f"{type(e).__name__}: {e}"))


def eq(actual, expected):
    if actual != expected:
        raise AssertionError(f"期待 {expected} / 実際 {actual}")
    return f"= {expected}"


def data():
    return [
        {"id": 1, "title": "期限切れ・高優先", "status": "pending", "due": "2026-08-01",
         "tags": ["a"], "priority": 2, "note": ""},
        {"id": 2, "title": "期限切れだが完了済み", "status": "done", "due": "2026-07-01",
         "tags": ["a"], "priority": 1, "note": ""},
        {"id": 3, "title": "期限なし", "status": "pending", "due": None,
         "tags": [], "priority": 1, "note": ""},
        {"id": 4, "title": "当日（期限切れではない）", "status": "pending", "due": "2026-08-14",
         "tags": [], "priority": 3, "note": ""},
        {"id": 5, "title": "未来", "status": "pending", "due": "2026-09-01",
         "tags": [], "priority": 1, "note": ""},
        {"id": 6, "title": "期限切れ・同日で優先度低", "status": "pending", "due": "2026-08-01",
         "tags": [], "priority": 4, "note": ""},
        {"id": 7, "title": "最も古い期限切れ", "status": "pending", "due": "2026-07-15",
         "tags": [], "priority": 5, "note": ""},
    ]


try:
    import taskstore as ts
except Exception as e:                           # noqa: BLE001 — 読めないこと自体が結果
    print(f"AUDIT NG taskstore が import できない :: {type(e).__name__}: {e}")
    sys.exit(1)


def overdue_ids(today="2026-08-14"):
    return [int(t["id"]) for t in ts.overdue_tasks(data(), today)]


def kept_ids():
    tasks = data()
    ts.overdue_tasks(tasks, "2026-08-14")
    return [int(t["id"]) for t in tasks]


def sig_gaps():
    gaps = []
    for name, params in EXPECTED_API.items():
        fn = getattr(ts, name, None)
        if fn is None or not callable(fn):
            continue
        actual = list(inspect.signature(fn).parameters)
        gaps.extend(f"{name}({p})" for p in params if p not in actual)
    return gaps


def csv_round_trip():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.csv")
        ts.export_csv(data(), path)
        return eq(ts.import_csv(path), data())


# --- 1. 頼んだ機能 ---
check("overdue_tasks が呼べる", lambda: eq(callable(getattr(ts, "overdue_tasks", None)), True))
check("期限切れだけを返す（完了済み・期限なし・当日・未来を除く）",
      lambda: eq(sorted(overdue_ids()), [1, 6, 7]))
check("due 昇順・同一 due は priority 昇順で並ぶ", lambda: eq(overdue_ids(), [7, 1, 6]))
check("today より前だけ（当日は含めない）", lambda: eq(overdue_ids("2026-08-01"), [7]))
check("期限切れが無ければ空を返す", lambda: eq(overdue_ids("2026-01-01"), []))
check("元のリストを変更しない", lambda: eq(kept_ids(), [1, 2, 3, 4, 5, 6, 7]))
check("stats(tasks, today) の overdue が3件", lambda: eq(ts.stats(data(), "2026-08-14")["overdue"], 3))
check("stats(tasks) は today 無しでも呼べて overdue=0", lambda: eq(ts.stats(data())["overdue"], 0))

# --- 2. 既存 API の生存（保守の本丸） ---
check("公開関数が1つも消えていない",
      lambda: eq([n for n in EXPECTED_API if not hasattr(ts, n)], []))
check("公開定数・例外が1つも消えていない",
      lambda: eq([n for n in EXPECTED_CONSTANTS if not hasattr(ts, n)], []))
check("既存関数の引数名が変わっていない", lambda: eq(sig_gaps(), []))

# --- 3. 与えたテストの範囲外の抜き取り（振る舞いの保存） ---
check("stats の既存の欄が保たれている",
      lambda: eq([ts.stats(data())[k] for k in ("total", "pending", "done", "tags")], [7, 6, 1, 1]))
check("import_csv/export_csv の往復が保たれている", csv_round_trip)
check("format_task の書式が保たれている",
      lambda: eq(ts.format_task(data()[0]), "[ ] #1   P2 2026-08-01 期限切れ・高優先 (a)"))
check("sort_tasks(key='due') が期限なしを末尾に置く",
      lambda: eq([int(t["id"]) for t in ts.sort_tasks(data(), key="due")], [2, 7, 1, 6, 4, 5, 3]))

for ok, claim, detail in RESULTS:
    print(f"AUDIT {'ok' if ok else 'NG'} {claim} :: {detail}")
sys.exit(0 if all(r[0] for r in RESULTS) else 1)
