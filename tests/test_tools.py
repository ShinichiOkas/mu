"""tools.py（検証用ツール）のユニットテスト。実ファイル操作は tmp_path で行う。

ツールは ToolResult（content: モデル向け散文 / ok: 成否 / facts: 機械可読な事実）を返す。
facts は実体（ディスクの stat・プロセスの exit code）から作る — 表象でなく実体（合意005）。
"""

from pathlib import Path

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


# --- 010: サイズ無制限化（窓を撤廃せず、動かせるようにする） --------------------
#
# 既定窓（_MAX_OUTPUT）は LLM 文脈の防衛として残す。代わりに read_file / list_dir に
# 行単位の窓（offset/limit, offset は 0 始まり＝読み飛ばす行数）を入れ、切り詰めたときは
# 「続きの offset」を content と facts の両方に出して辿れるようにする（合意010）。

@pytest.fixture
def big_file(tmp_path):
    """既定窓（4000 文字）を確実に超える 500 行のファイル。各行は 'line NNN' + 改行。"""
    p = tmp_path / "big.txt"
    p.write_text("".join(f"line {i:03d}\n" for i in range(500)), encoding="utf-8")
    return p


def test_read_offset_skips_lines(big_file):
    # 続きがあるので末尾に案内文が付く（本文はその手前まで）。
    r = tools.read_file(str(big_file), offset=200, limit=3)
    assert r.content.split("\n...(")[0] == "line 200\nline 201\nline 202\n"
    assert r.facts["offset"] == 200
    assert r.facts["lines"] == 3


def test_read_limit_caps_the_number_of_lines(big_file):
    r = tools.read_file(str(big_file), limit=10)
    assert r.content.startswith("line 000\n")
    assert r.facts["lines"] == 10


def test_read_reports_total_lines_regardless_of_the_window(big_file):
    # 位置感覚（全体のどこを見ているか）は窓の大きさに依らず分かる必要がある。
    r = tools.read_file(str(big_file), offset=10, limit=1)
    assert r.facts["total_lines"] == 500


def test_read_truncated_result_points_to_the_continuation(big_file):
    r = tools.read_file(str(big_file), limit=5)
    assert r.facts["truncated"] is True
    assert r.facts["next_offset"] == 5
    assert "offset=5" in r.content  # モデルにも散文で見える


def test_read_last_window_has_no_continuation(big_file):
    r = tools.read_file(str(big_file), offset=498)
    assert r.facts["truncated"] is False
    assert r.facts["next_offset"] is None


def test_read_default_window_truncates_but_stays_reachable(big_file):
    # 引数を省略した既定の呼び出しは従来どおり切り詰めるが、続きが示される。
    r = tools.read_file(str(big_file))
    assert r.facts["truncated"] is True
    assert r.facts["next_offset"] > 0


def test_read_can_reach_every_line_of_a_large_file(big_file):
    # 完了条件: next_offset を辿るだけで全行が復元できる（どの位置も読める）。
    collected, offset, rounds = [], 0, 0
    while offset is not None and rounds < 100:
        r = tools.read_file(str(big_file), offset=offset)
        collected.append(r.content.split("\n...(")[0])
        offset = r.facts["next_offset"]
        rounds += 1
    assert "".join(collected) == big_file.read_text(encoding="utf-8")


def test_read_offset_beyond_end_is_empty_but_not_an_error(big_file):
    r = tools.read_file(str(big_file), offset=10_000)
    assert r.ok is True
    assert r.facts["lines"] == 0
    assert r.facts["total_lines"] == 500
    assert r.facts["next_offset"] is None


def test_read_does_not_split_a_line_longer_than_the_window(tmp_path):
    # 行を割ると offset ではその続きを指せず、辿る手段が消える（合意010 AI 判断）。
    # よって窓より長い1行は丸ごと返し、実測の文字数を facts に出す。
    p = tmp_path / "long_line.txt"
    p.write_text("x" * 10_000 + "\n" + "tail\n", encoding="utf-8")
    r = tools.read_file(str(p), limit=1)
    assert r.content.split("\n...(")[0] == "x" * 10_000 + "\n"
    assert r.facts["chars"] == 10_001  # 窓（4000）より長くても割らずに丸ごと返す


def test_read_short_file_is_returned_whole_without_a_notice(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text("hello", encoding="utf-8")
    r = tools.read_file(str(p))
    assert r.content == "hello"  # 案内文は切り詰めたときだけ付く
    assert r.facts["truncated"] is False


# --- write_file の mode（末尾追加） ---

def test_write_append_adds_to_the_end(tmp_path):
    p = tmp_path / "a.txt"
    tools.write_file(str(p), "first\n")
    tools.write_file(str(p), "second\n", mode="append")
    assert p.read_text(encoding="utf-8") == "first\nsecond\n"


def test_write_append_creates_the_file_when_missing(tmp_path):
    p = tmp_path / "sub" / "new.txt"
    r = tools.write_file(str(p), "x", mode="append")
    assert r.ok is True
    assert p.read_text(encoding="utf-8") == "x"


def test_write_append_facts_report_added_and_total_bytes(tmp_path):
    p = tmp_path / "a.txt"
    tools.write_file(str(p), "abc")
    r = tools.write_file(str(p), "de", mode="append")
    assert r.facts["appended"] == 2
    assert r.facts["bytes"] == p.stat().st_size == 5  # bytes は従来どおりディスク実体
    assert r.facts["mode"] == "append"


def test_write_append_accumulates_beyond_a_single_call(tmp_path):
    # 完了条件: 1回の生成に収まらない長さの成果物を積み上げられる。
    p = tmp_path / "report.md"
    for i in range(50):
        tools.write_file(str(p), f"section {i}\n" + "body " * 200 + "\n", mode="append")
    assert p.stat().st_size > 50_000
    assert tools.read_file(str(p)).facts["total_lines"] == 100


def test_write_mode_aliases_are_accepted(tmp_path):
    p = tmp_path / "a.txt"
    tools.write_file(str(p), "1\n")
    tools.write_file(str(p), "2\n", mode="a")
    assert p.read_text(encoding="utf-8") == "1\n2\n"


def test_write_unknown_mode_is_an_error_and_does_not_touch_the_file(tmp_path):
    # 未知の値を黙って上書きに倒すと破壊が起きる。止めて正しい値を案内する。
    p = tmp_path / "a.txt"
    p.write_text("keep", encoding="utf-8")
    r = tools.write_file(str(p), "boom", mode="clobber")
    assert r.ok is False
    assert "append" in r.content
    assert p.read_text(encoding="utf-8") == "keep"


def test_protected_file_cannot_be_appended(protected):
    # 追記も内容改変である。保護は mode に依らず効く。
    r = tools.write_file(str(protected), "extra", mode="append")
    assert r.ok is False
    assert protected.read_text(encoding="utf-8") == "original"


def test_edit_missing_old_suggests_appending(tmp_path):
    p = tmp_path / "d.txt"
    p.write_text("abc", encoding="utf-8")
    r = tools.edit_file(str(p), "zzz", "y")
    assert r.ok is False
    assert "append" in r.content  # 実際に起きる誤用（末尾追加したい）への steering


# --- execute_command の長い出力 ---

def _long_output_command(chars=12_000):
    return f"'x' * {chars}"  # PowerShell: 長い1行を吐く


def test_execute_long_output_is_truncated_but_kept_whole_on_disk():
    r = tools.execute_command(_long_output_command())
    assert r.facts["truncated"] is True
    assert r.facts["chars"] > 12_000
    saved = Path(r.facts["output_path"])
    assert saved.exists()
    assert "x" * 12_000 in saved.read_text(encoding="utf-8")
    assert r.facts["output_path"] in r.content  # モデルが辿れるようパスを散文にも出す
    saved.unlink()


def test_execute_full_output_is_reachable_with_read_file():
    r = tools.execute_command(_long_output_command())
    saved = r.facts["output_path"]
    assert tools.read_file(saved, offset=0).ok is True
    Path(saved).unlink()


def test_execute_short_output_leaves_no_file():
    r = tools.execute_command("echo hi")
    assert r.facts["truncated"] is False
    assert r.facts.get("output_path") is None


# --- list_dir の窓 ---

@pytest.fixture
def many_files(tmp_path):
    for i in range(300):
        (tmp_path / f"f{i:03d}.txt").write_text("x", encoding="utf-8")
    return tmp_path


def test_list_dir_offset_and_limit(many_files):
    r = tools.list_dir(str(many_files), offset=10, limit=2)
    assert r.facts["entries"] == 2
    assert "f010.txt" in r.content and "f011.txt" in r.content
    assert "f012.txt" not in r.content


def test_list_dir_default_window_points_to_the_continuation(many_files):
    r = tools.list_dir(str(many_files))
    assert r.facts["truncated"] is True
    assert r.facts["next_offset"] > 0
    assert r.facts["total_entries"] == 300


def test_list_dir_small_directory_is_listed_whole(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    r = tools.list_dir(str(tmp_path))
    assert r.facts["truncated"] is False
    assert r.facts["next_offset"] is None
