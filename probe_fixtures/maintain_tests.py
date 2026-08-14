"""taskstore の既存仕様を固定するテスト。このファイルは変更禁止（読み取り専用）。"""
import os
import tempfile
import unittest

import taskstore as ts


def sample():
    return [
        {"id": 1, "title": "見積を送る", "status": "pending", "due": "2026-08-20",
         "tags": ["営業"], "priority": 2, "note": "A社"},
        {"id": 2, "title": "議事録をまとめる", "status": "done", "due": "2026-08-10",
         "tags": ["社内", "記録"], "priority": 3, "note": ""},
        {"id": 3, "title": "請求書を確認", "status": "pending", "due": None,
         "tags": ["経理"], "priority": 1, "note": "月末"},
        {"id": 4, "title": "資料を印刷", "status": "pending", "due": "2026-08-15",
         "tags": ["社内"], "priority": 5, "note": ""},
    ]


class TestBasics(unittest.TestCase):
    def test_next_id_empty(self):
        self.assertEqual(ts.next_id([]), 1)

    def test_next_id_after_max(self):
        self.assertEqual(ts.next_id(sample()), 5)

    def test_add_task_defaults(self):
        tasks = []
        task = ts.add_task(tasks, "新しい仕事")
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["priority"], 3)
        self.assertEqual(task["tags"], [])
        self.assertIsNone(task["due"])
        self.assertEqual(len(tasks), 1)

    def test_add_task_strips_title(self):
        tasks = []
        self.assertEqual(ts.add_task(tasks, "  余白あり  ")["title"], "余白あり")

    def test_add_task_rejects_empty_title(self):
        with self.assertRaises(ts.TaskError):
            ts.add_task([], "   ")

    def test_add_task_rejects_bad_priority(self):
        with self.assertRaises(ts.TaskError):
            ts.add_task([], "だめ", priority=9)

    def test_get_task(self):
        self.assertEqual(ts.get_task(sample(), 3)["title"], "請求書を確認")

    def test_get_task_missing(self):
        with self.assertRaises(ts.TaskError):
            ts.get_task(sample(), 99)


class TestUpdate(unittest.TestCase):
    def test_update_changes_field(self):
        tasks = sample()
        ts.update_task(tasks, 1, priority=4)
        self.assertEqual(ts.get_task(tasks, 1)["priority"], 4)

    def test_update_rejects_id(self):
        with self.assertRaises(ts.TaskError):
            ts.update_task(sample(), 1, id=7)

    def test_update_rejects_unknown_field(self):
        with self.assertRaises(ts.TaskError):
            ts.update_task(sample(), 1, owner="山田")

    def test_update_validates(self):
        with self.assertRaises(ts.TaskError):
            ts.update_task(sample(), 1, due="2026/08/20")

    def test_delete(self):
        tasks = sample()
        ts.delete_task(tasks, 2)
        self.assertEqual([t["id"] for t in tasks], [1, 3, 4])

    def test_complete_and_reopen(self):
        tasks = sample()
        ts.complete_task(tasks, 1)
        self.assertEqual(ts.get_task(tasks, 1)["status"], "done")
        ts.reopen_task(tasks, 1)
        self.assertEqual(ts.get_task(tasks, 1)["status"], "pending")

    def test_complete_twice_raises(self):
        with self.assertRaises(ts.TaskError):
            ts.complete_task(sample(), 2)

    def test_reopen_pending_raises(self):
        with self.assertRaises(ts.TaskError):
            ts.reopen_task(sample(), 1)


class TestQuery(unittest.TestCase):
    def test_list_by_status(self):
        self.assertEqual([t["id"] for t in ts.list_tasks(sample(), status="pending")], [1, 3, 4])

    def test_list_by_tag(self):
        self.assertEqual([t["id"] for t in ts.list_tasks(sample(), tag="社内")], [2, 4])

    def test_list_by_priority_max(self):
        self.assertEqual([t["id"] for t in ts.list_tasks(sample(), priority_max=2)], [1, 3])

    def test_list_rejects_bad_status(self):
        with self.assertRaises(ts.TaskError):
            ts.list_tasks(sample(), status="unknown")

    def test_search_is_case_insensitive_and_covers_note(self):
        tasks = sample()
        self.assertEqual([t["id"] for t in ts.search_tasks(tasks, "a社")], [1])
        self.assertEqual([t["id"] for t in ts.search_tasks(tasks, "月末")], [3])

    def test_sort_by_priority(self):
        self.assertEqual([t["id"] for t in ts.sort_tasks(sample())], [3, 1, 2, 4])

    def test_sort_by_due_puts_none_last(self):
        self.assertEqual([t["id"] for t in ts.sort_tasks(sample(), key="due")], [2, 4, 1, 3])

    def test_sort_does_not_mutate(self):
        tasks = sample()
        ts.sort_tasks(tasks, key="due")
        self.assertEqual([t["id"] for t in tasks], [1, 2, 3, 4])

    def test_sort_rejects_bad_key(self):
        with self.assertRaises(ts.TaskError):
            ts.sort_tasks(sample(), key="owner")

    def test_tag_counts_order(self):
        self.assertEqual(list(ts.tag_counts(sample()).items()),
                         [("社内", 2), ("営業", 1), ("経理", 1), ("記録", 1)])


class TestStats(unittest.TestCase):
    def test_counts(self):
        s = ts.stats(sample())
        self.assertEqual(s["total"], 4)
        self.assertEqual(s["pending"], 3)
        self.assertEqual(s["done"], 1)

    def test_tags_and_average(self):
        s = ts.stats(sample())
        self.assertEqual(s["tags"], 4)
        self.assertAlmostEqual(s["avg_priority"], 2.75)

    def test_empty(self):
        s = ts.stats([])
        self.assertEqual(s["total"], 0)
        self.assertEqual(s["avg_priority"], 0)


class TestIO(unittest.TestCase):
    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tasks.json")
            self.assertEqual(ts.save_tasks(path, sample()), 4)
            self.assertEqual(ts.load_tasks(path), sample())

    def test_load_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ts.load_tasks(os.path.join(d, "nope.json")), [])

    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tasks.csv")
            ts.export_csv(sample(), path)
            self.assertEqual(ts.import_csv(path), sample())

    def test_format_task(self):
        line = ts.format_task(sample()[0])
        self.assertIn("#1", line)
        self.assertIn("P2", line)
        self.assertIn("2026-08-20", line)
        self.assertIn("見積を送る", line)

    def test_format_table_lines(self):
        self.assertEqual(len(ts.format_table(sample()).splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
