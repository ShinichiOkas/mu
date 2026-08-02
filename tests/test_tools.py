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


# --- 入力ファイル保護（合意006 決定④の解除条件発火により実装。コード側・決定論） ---

@pytest.fixture
def protected(tmp_path):
    p = tmp_path / "input.csv"
    p.write_text("original", encoding="utf-8")
    tools.protect([str(p)])
    yield p
    tools.clear_protection()


def test_protected_file_cannot_be_written(protected):
    r = tools.write_file(str(protected), "overwritten")
    assert r.ok is False
    assert "protected" in r.content or "保護" in r.content
    assert protected.read_text(encoding="utf-8") == "original"  # 実体は無傷


def test_protected_file_cannot_be_edited(protected):
    r = tools.edit_file(str(protected), "original", "changed")
    assert r.ok is False
    assert protected.read_text(encoding="utf-8") == "original"


def test_protection_is_path_normalized(protected, tmp_path, monkeypatch):
    # 相対パス経由でも保護される（resolve で照合）。
    monkeypatch.chdir(tmp_path)
    r = tools.write_file("input.csv", "x")
    assert r.ok is False
    assert protected.read_text(encoding="utf-8") == "original"


def test_unprotected_files_still_writable(protected, tmp_path):
    r = tools.write_file(str(tmp_path / "other.txt"), "ok")
    assert r.ok is True


def test_protected_file_is_still_readable(protected):
    assert tools.read_file(str(protected)).content == "original"


def test_tools_list_is_l1_pairs():
    # L1 が使える形式: (callable, usage_text) のペアのリスト
    assert len(tools.TOOLS) == 5
    for func, usage in tools.TOOLS:
        assert callable(func)
        assert isinstance(usage, str) and usage


# --- B2（合意007）: 保護の意味論と、破れの検出 ---------------------------------
#
# protect() が守るのは「列挙したファイルの内容不変」であって、ディレクトリの不変ではない。
# 新規ファイルの作成（H4 のスコープ逸脱）も、execute_command のシェルリダイレクトも通る。
# 塞ぐ（能力を削る）のではなく、破れたことが見えるようにする（合意007 決めたこと4）。

def test_no_violations_when_protected_files_are_untouched(protected):
    assert tools.protection_violations() == []


def test_violation_is_detected_when_a_protected_file_changes_behind_the_tools(protected):
    # write_file/edit_file を通らない改変（シェルリダイレクト等）は拒否できない。検出はできる。
    protected.write_text("rewritten behind the tool layer", encoding="utf-8")
    violations = tools.protection_violations()
    assert [v["status"] for v in violations] == ["modified"]
    assert str(protected) in violations[0]["path"]


def test_violation_is_detected_when_a_protected_file_disappears(protected):
    protected.unlink()
    violations = tools.protection_violations()
    assert [v["status"] for v in violations] == ["missing"]


def test_restoring_the_original_content_clears_the_violation(protected):
    original = protected.read_text(encoding="utf-8")
    protected.write_text("broken", encoding="utf-8")
    assert tools.protection_violations()
    protected.write_text(original, encoding="utf-8")
    assert tools.protection_violations() == []


def test_new_files_are_not_prevented_by_protection(protected, tmp_path):
    # 意味論の明示: ディレクトリ不変は保証しない（H4 の新規ファイル追加は防がない）。
    r = tools.write_file(str(tmp_path / "extra.md"), "テスト用に足したファイル")
    assert r.ok is True
    assert tools.protection_violations() == []
