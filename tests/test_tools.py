"""tools.py（検証用ツール）のユニットテスト。実ファイル操作は tmp_path で行う。

ツールは ToolResult（content: モデル向け散文 / ok: 成否 / facts: 機械可読な事実）を返す。
facts は実体（ディスクの stat・プロセスの exit code）から作る — 表象でなく実体（合意005）。
"""

import pytest

import tools


def test_write_then_read(tmp_path):
    p = tmp_path / "a.txt"
    tools.write_file(str(p), "hello")
    assert tools.read_file(str(p)).content == "hello"


def test_write_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "b.txt"
    tools.write_file(str(p), "x")
    assert p.read_text(encoding="utf-8") == "x"


def test_write_facts_report_bytes_on_disk(tmp_path):
    # facts の bytes は len(content) でなくディスクの stat から（書けた実体の証拠）。
    p = tmp_path / "a.txt"
    r = tools.write_file(str(p), "héllo")  # UTF-8 で 6 bytes（5 chars）
    assert r.ok is True
    assert r.facts["bytes"] == p.stat().st_size == 6
    assert r.facts["path"] == str(p)
    assert r.facts["action"] == "write"


def test_read_facts_report_chars_and_truncation(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x" * 10, encoding="utf-8")
    r = tools.read_file(str(p))
    assert r.ok is True
    assert r.facts["chars"] == 10
    assert r.facts["truncated"] is False


def test_edit_replaces_all(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("foo bar foo", encoding="utf-8")
    r = tools.edit_file(str(p), "foo", "baz")
    assert p.read_text(encoding="utf-8") == "baz bar baz"
    assert r.ok is True
    assert r.facts["replacements"] == 2


def test_edit_missing_old_is_not_ok_and_leaves_file(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("abc", encoding="utf-8")
    r = tools.edit_file(str(p), "zzz", "y")
    assert r.ok is False
    assert "not found" in r.content
    assert p.read_text(encoding="utf-8") == "abc"  # 変更されない


def test_execute_command_echo():
    r = tools.execute_command("echo hello")
    assert r.ok is True
    assert r.facts["exit"] == 0
    assert "hello" in r.content


def test_execute_command_nonzero_exit_is_not_ok():
    r = tools.execute_command("exit 3")
    assert r.ok is False
    assert r.facts["exit"] == 3


def test_list_dir_lists_entries(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    r = tools.list_dir(str(tmp_path))
    assert "a.txt" in r.content
    assert "sub" in r.content
    assert r.ok is True


def test_list_dir_missing_path_is_not_ok():
    r = tools.list_dir("no_such_dir_xyz_123")
    assert r.ok is False
    assert "not found" in r.content


def test_read_missing_file_raises():
    with pytest.raises(Exception):
        tools.read_file("no_such_file_xyz_123.txt")


def test_tools_list_is_l1_pairs():
    # L1 が使える形式: (callable, usage_text) のペアのリスト
    assert len(tools.TOOLS) == 5
    for func, usage in tools.TOOLS:
        assert callable(func)
        assert isinstance(usage, str) and usage
