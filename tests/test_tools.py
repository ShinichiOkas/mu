"""tools.py（検証用ツール）のユニットテスト。実ファイル操作は tmp_path で行う。"""

import pytest

import tools


def test_write_then_read(tmp_path):
    p = tmp_path / "a.txt"
    tools.write_file(str(p), "hello")
    assert tools.read_file(str(p)) == "hello"


def test_write_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "b.txt"
    tools.write_file(str(p), "x")
    assert p.read_text(encoding="utf-8") == "x"


def test_edit_replaces_all(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("foo bar foo", encoding="utf-8")
    msg = tools.edit_file(str(p), "foo", "baz")
    assert p.read_text(encoding="utf-8") == "baz bar baz"
    assert "2" in msg


def test_edit_missing_old_reports_error_and_leaves_file(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("abc", encoding="utf-8")
    msg = tools.edit_file(str(p), "zzz", "y")
    assert "not found" in msg
    assert p.read_text(encoding="utf-8") == "abc"  # 変更されない


def test_execute_command_echo():
    out = tools.execute_command("echo hello")
    assert "exit=0" in out
    assert "hello" in out


def test_list_dir_lists_entries(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    out = tools.list_dir(str(tmp_path))
    assert "a.txt" in out
    assert "sub" in out


def test_list_dir_missing_path_reports_error():
    assert "not found" in tools.list_dir("no_such_dir_xyz_123")


def test_read_missing_file_raises():
    with pytest.raises(Exception):
        tools.read_file("no_such_file_xyz_123.txt")


def test_tools_list_is_l1_pairs():
    # L1 が使える形式: (callable, usage_text) のペアのリスト
    assert len(tools.TOOLS) == 5
    for func, usage in tools.TOOLS:
        assert callable(func)
        assert isinstance(usage, str) and usage
