"""tools.py（検証用ツール）のユニットテスト。実ファイル操作は tmp_path で行う。

ツールは ToolResult（content: モデル向け散文 / ok: 成否 / facts: 機械可読な事実）を返す。
facts は実体（ディスクの stat・プロセスの exit code）から作る — 表象でなく実体（合意005）。
"""

import json
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
    assert len(tools.TOOLS) == 7
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


def _bypass(path, write):
    """防ぐ層を意図的に回避する（attrib -R 相当）。二層構造の外側を外してから触る。"""
    import os
    import stat
    os.chmod(path, stat.S_IWRITE)
    write()


def test_violation_is_detected_when_a_protected_file_changes_behind_the_tools(protected):
    # 016 以降、単なる書き込みは OS 層で止まる（上のテスト群）。だが属性を外せば回避できる——
    # 実測で attrib -R / Remove-Item -Force は通る。**防げないものは検出する**（二層構造の外側）。
    _bypass(protected, lambda: protected.write_text("rewritten behind the tool layer", encoding="utf-8"))
    violations = tools.protection_violations()
    assert [v["status"] for v in violations] == ["modified"]
    assert str(protected) in violations[0]["path"]


def test_violation_is_detected_when_a_protected_file_disappears(protected):
    _bypass(protected, protected.unlink)
    violations = tools.protection_violations()
    assert [v["status"] for v in violations] == ["missing"]


def test_restoring_the_original_content_clears_the_violation(protected):
    original = protected.read_text(encoding="utf-8")
    _bypass(protected, lambda: protected.write_text("broken", encoding="utf-8"))
    assert tools.protection_violations()
    protected.write_text(original, encoding="utf-8")
    assert tools.protection_violations() == []   # 検出は内容の一致で決まる（属性ではない）


# --- 016: 防ぐ層（OS の read-only）。tools 層を通らない改変も止める ---------------
#
# 二層構造（師匠）: 原本は金庫に入れる（防ぐ）。それでも監査はする（検出）。
# 防ぐ層は偶発的・無自覚な改変を確実に止めるが、意図的な回避（attrib -R）は止められない。
# だから検出層（protection_violations）を残す。合意007 の否定ではなく、その上に足す。

def test_protected_file_cannot_be_written_outside_the_tools_layer(protected):
    # 015 の実害: 実装者が test_inventory.py を書いて python で実行し、入力を上書きした。
    # tools 層を通らないので write_file の拒否では止まらない。OS 側で止める。
    with pytest.raises(OSError):
        with open(protected, "w", encoding="utf-8") as f:
            f.write("破壊")
    assert protected.read_text(encoding="utf-8") == "original"


def test_protected_file_cannot_be_deleted_outside_the_tools_layer(protected):
    with pytest.raises(OSError):
        protected.unlink()
    assert protected.exists()


def test_protected_file_cannot_be_written_by_a_shell_command(protected):
    # execute_command 経由（合意007 で「防げない」とした経路）が実際に防がれること。
    r = tools.execute_command(f'Set-Content -Path "{protected}" -Value broken')
    assert r.ok is False
    assert protected.read_text(encoding="utf-8") == "original"


def test_clear_protection_restores_writability(tmp_path):
    p = tmp_path / "input.csv"
    p.write_text("original", encoding="utf-8")
    tools.protect([str(p)])
    tools.clear_protection()
    p.write_text("編集できる", encoding="utf-8")   # 例外が出ないこと
    assert p.read_text(encoding="utf-8") == "編集できる"


def test_clear_protection_keeps_a_file_that_was_already_read_only(tmp_path):
    # 保護前の状態へ戻す。元々 read-only だったものを書けるようにして返さない。
    import os
    import stat
    p = tmp_path / "frozen.csv"
    p.write_text("original", encoding="utf-8")
    os.chmod(p, stat.S_IREAD)
    tools.protect([str(p)])
    tools.clear_protection()
    with pytest.raises(OSError):
        p.write_text("x", encoding="utf-8")
    os.chmod(p, stat.S_IWRITE)   # 後始末


def test_protecting_a_missing_path_does_not_raise(tmp_path):
    tools.protect([str(tmp_path / "no_such_input.csv")])   # 登録だけ。検出層が missing で拾う
    assert tools.protection_violations() == []
    tools.clear_protection()


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


# --- 011: web 検索・取得 ------------------------------------------------------
#
# 3層で書く（合意011 C）。ここでは**純粋整形**（応答 → 文字列/構造）だけを固定サンプルで検証する。
# 実 HTTP を叩く I/O ヘルパーは live マーカー側（下部）に置き、ネット未接続ならスキップする。

# lite.duckduckgo.com の実応答から採った断片（2026-08-05 取得）。
_DDG_SAMPLE = """
<table>
  <tr><td class="result-count">1.&nbsp;</td>
      <td><a rel="nofollow" href="https://www.python.org/" class='result-link'>Welcome to Python.org</a></td></tr>
  <tr><td>&nbsp;</td>
      <td class='result-snippet'>The official home of the <b>Python</b> Programming Language.</td></tr>
  <tr><td class="result-count">2.&nbsp;</td>
      <td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F&amp;rut=abc" class='result-link'>3.14 Documentation</a></td></tr>
  <tr><td>&nbsp;</td>
      <td class='result-snippet'>The official <b>Python</b> docs &amp; tutorial.</td></tr>
</table>
"""


def test_ddg_parser_extracts_title_url_and_snippet():
    results = tools._ddg_results(_DDG_SAMPLE)
    assert results[0]["title"] == "Welcome to Python.org"
    assert results[0]["url"] == "https://www.python.org/"
    assert "Programming Language" in results[0]["snippet"]


def test_ddg_parser_unwraps_the_redirect_url():
    # DDG がリダイレクト URL を挟む場合がある。実 URL に戻さないとモデルが fetch_url に渡せない。
    results = tools._ddg_results(_DDG_SAMPLE)
    assert results[1]["url"] == "https://docs.python.org/3/"


def test_ddg_parser_unescapes_entities_in_text():
    results = tools._ddg_results(_DDG_SAMPLE)
    assert "docs & tutorial" in results[1]["snippet"]  # &amp; が戻っている
    assert "<b>" not in results[1]["snippet"]  # 強調タグは落ちている


def test_ddg_parser_returns_empty_list_for_unknown_markup():
    # 構造が変わったら「0件」になる。ここでは落ちないことだけを担保し、
    # 「0件＝取れなかったかもしれない」の判断は呼び出し側（web_search）が持つ。
    assert tools._ddg_results("<html><body>no results here</body></html>") == []


_HTML_SAMPLE = """
<html><head><title>T</title><style>body{color:red}</style></head>
<body><nav>Home | About</nav>
<h1>Heading</h1>
<p>Hello&nbsp;&amp; welcome.</p>
<script>alert('x')</script>
<footer>(c) 2026</footer></body></html>
"""


def test_html_to_text_drops_scripts_styles_and_chrome():
    text = tools._html_to_text(_HTML_SAMPLE)
    assert "alert" not in text
    assert "color:red" not in text
    assert "Home | About" not in text
    assert "(c) 2026" not in text


def test_html_to_text_keeps_the_body_and_unescapes_entities():
    text = tools._html_to_text(_HTML_SAMPLE)
    assert "Heading" in text
    assert "Hello & welcome." in text
    assert "<" not in text  # タグは残らない


def test_html_to_text_collapses_blank_lines():
    text = tools._html_to_text("<p>a</p>\n\n\n\n<p>b</p>")
    assert text == "a\nb"


def test_format_search_results_is_readable_and_carries_urls():
    formatted = tools._format_results(
        [{"title": "T1", "url": "https://a.example", "snippet": "s1"}]
    )
    assert "1." in formatted and "T1" in formatted
    assert "https://a.example" in formatted
    assert "s1" in formatted


def test_web_tools_are_registered():
    names = [func.__name__ for func, _ in tools.TOOLS]
    assert "web_search" in names
    assert "fetch_url" in names


# --- I/O（実ネット。未接続・レート制限ならスキップ） ---

live = pytest.mark.live


@live
def test_web_search_returns_real_results():
    r = tools.web_search("Python programming language", limit=5)
    if not r.ok:
        pytest.skip(f"検索が取れない環境（レート制限等）: {r.content[:80]}")
    assert r.facts["results"] > 0
    assert "http" in r.content


@live
def test_fetch_url_returns_body_text():
    r = tools.fetch_url("https://example.com/")
    if not r.ok:
        pytest.skip(f"取得できない環境: {r.content[:80]}")
    assert r.facts["status"] == 200
    assert "Example Domain" in r.content


@live
def test_fetch_url_reports_http_errors_honestly():
    # 取れないサイトは実在する（Wikipedia は UA を変えても 403）。空文字で成功を装わない。
    # 相手は「404 を返すことが安定している先」を選ぶ（外部サービスの一時障害でテストを揺らさない）。
    r = tools.fetch_url("https://example.com/no-such-page-mu-011")
    if r.facts.get("status") is None:
        pytest.skip("外部サービスに到達できない")
    assert r.ok is False
    assert r.facts["status"] == 404
    assert "404" in r.content  # モデルにも理由が見える


# --- 015: LLM で実装された検査器（judge） ------------------------------------
#
# 決定論の検査器が書けない性質（妥当性・網羅性）のための道具。**文脈非共有が本体**——
# 渡すのは要件と対象の中身だけで、走行履歴・実装者の言い分・過去の失敗は渡さない。
# 別モデルを前提にしない（環境依存になるため）。同一モデルでも成立することを設計要件に置く。

class _FakeL0:
    """judge の LLM 呼び出しの代役。渡された messages を記録する。"""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def chat(self, model, messages, **kwargs):
        import types as _t
        self.calls.append({"model": model, "messages": messages, "kwargs": kwargs})
        return _t.SimpleNamespace(message=_t.SimpleNamespace(content=json.dumps(self._payload)))


def _judge_for(payload, tmp_path, text="本文", model="m"):
    p = tmp_path / "target.md"
    p.write_text(text, encoding="utf-8")
    l0 = _FakeL0(payload)
    return tools.make_judge(l0, model), l0, p


def test_judge_returns_the_verdict_and_reason(tmp_path):
    judge, _, p = _judge_for({"verdict": "pass", "reason": "満たしている", "evidence": "3行目"}, tmp_path)
    r = judge("結論が書かれていること", str(p))
    assert r.ok is True
    assert r.facts["verdict"] == "pass"
    assert "満たしている" in r.content


def test_judge_fail_is_not_ok(tmp_path):
    judge, _, p = _judge_for({"verdict": "fail", "reason": "結論が無い", "evidence": ""}, tmp_path)
    r = judge("結論が書かれていること", str(p))
    assert r.ok is False
    assert r.facts["verdict"] == "fail"


def test_judge_uncertain_is_preserved_not_collapsed_into_pass(tmp_path):
    # 「判定できない」を潰さない（QA の既存規範と揃える）。
    judge, _, p = _judge_for({"verdict": "uncertain", "reason": "読み取れない", "evidence": ""}, tmp_path)
    r = judge("網羅されていること", str(p))
    assert r.facts["verdict"] == "uncertain"
    assert r.ok is False   # 不明を合格にしない


def test_judge_sends_only_the_requirement_and_the_target(tmp_path):
    # 文脈非共有が本体。走行の経緯が混ざると「頑張ったから」が効いてしまう。
    judge, l0, p = _judge_for(
        {"verdict": "pass", "reason": "ok", "evidence": "x"}, tmp_path, text="対象の中身マーカー"
    )
    judge("要件マーカー", str(p))
    sent = json.dumps(l0.calls[0]["messages"], ensure_ascii=False)
    assert "要件マーカー" in sent
    assert "対象の中身マーカー" in sent
    assert len(l0.calls[0]["messages"]) == 2          # system と user だけ（履歴なし）
    assert l0.calls[0]["messages"][0]["role"] == "system"


def test_judge_uses_the_run_model_when_none_is_given(tmp_path):
    # 別モデルが使える環境かは環境依存。省略時は走行の既定モデルで動く（師匠の補正）。
    p = tmp_path / "t.md"
    p.write_text("x", encoding="utf-8")
    l0 = _FakeL0({"verdict": "pass", "reason": "ok", "evidence": "x"})
    judge = tools.make_judge(l0, "default-model")
    judge("要件", str(p))
    assert l0.calls[0]["model"] == "default-model"


def test_judge_missing_target_is_an_error_not_a_pass(tmp_path):
    l0 = _FakeL0({"verdict": "pass", "reason": "ok", "evidence": "x"})
    judge = tools.make_judge(l0, "m")
    r = judge("要件", str(tmp_path / "no_such_file.md"))
    assert r.ok is False
    assert l0.calls == []       # 読めないものを LLM に判定させない


def test_judge_unparseable_response_is_uncertain_not_pass(tmp_path):
    # 壊れた応答を合格に倒さない（証拠が無いことを合格にしない）。
    import types as _t

    class Broken:
        calls = []
        def chat(self, model, messages, **kwargs):
            return _t.SimpleNamespace(message=_t.SimpleNamespace(content="not json at all"))

    p = tmp_path / "t.md"
    p.write_text("x", encoding="utf-8")
    r = tools.make_judge(Broken(), "m")("要件", str(p))
    assert r.facts["verdict"] == "uncertain"
    assert r.ok is False


def test_judge_reads_a_prose_answer_when_the_model_ignores_the_schema(tmp_path):
    # 実測: gemma4:31b-cloud は format=（構造化出力）を守らず散文を返すことがある。
    # 判定者のモデルを選べる環境を前提にしないので、散文でも読めなければならない。
    import types as _t

    class Prose:
        def chat(self, model, messages, **kwargs):
            return _t.SimpleNamespace(message=_t.SimpleNamespace(
                content="VERDICT: fail\nEVIDENCE: \nREASON: 結論の節が空である"))

    p = tmp_path / "t.md"
    p.write_text("# 結論\n\n", encoding="utf-8")
    r = tools.make_judge(Prose(), "m")("結論が書かれていること", str(p))
    assert r.facts["verdict"] == "fail"
    assert "結論の節が空" in r.content


def test_judge_prose_pass_is_read_as_pass(tmp_path):
    import types as _t

    class Prose:
        def chat(self, model, messages, **kwargs):
            return _t.SimpleNamespace(message=_t.SimpleNamespace(
                content="**VERDICT:** pass\nEVIDENCE: Ollama を使い続けるべき\nREASON: 明記されている"))

    p = tmp_path / "t.md"
    p.write_text("x", encoding="utf-8")
    r = tools.make_judge(Prose(), "m")("結論があること", str(p))
    assert r.facts["verdict"] == "pass"          # 装飾（**）は許容
    assert r.facts["evidence"].startswith("Ollama")


def test_judge_answer_without_a_verdict_line_is_uncertain(tmp_path):
    import types as _t

    class Vague:
        def chat(self, model, messages, **kwargs):
            return _t.SimpleNamespace(message=_t.SimpleNamespace(
                content="Yes, the text has a conclusion."))   # 実測で観測された形

    p = tmp_path / "t.md"
    p.write_text("x", encoding="utf-8")
    r = tools.make_judge(Vague(), "m")("結論があること", str(p))
    assert r.facts["verdict"] == "uncertain"     # 判定語が無ければ合格にしない
    assert r.ok is False


def test_judge_prompt_demands_evidence_and_defaults_to_fail(tmp_path):
    # 既定を fail 側に置く（LLM は pass に倒れやすい）。system にその規範が入っていること。
    judge, l0, p = _judge_for({"verdict": "pass", "reason": "ok", "evidence": "x"}, tmp_path)
    judge("要件", str(p))
    system = l0.calls[0]["messages"][0]["content"]
    assert "evidence" in system.lower()
    assert "fail" in system.lower()


@live
def test_fetch_url_long_page_is_saved_whole_and_reachable():
    r = tools.fetch_url("https://docs.python.org/3/whatsnew/3.13.html")
    if not r.ok:
        pytest.skip("取得できない環境")
    assert r.facts["truncated"] is True
    saved = Path(r.facts["output_path"])
    assert saved.exists() and saved.stat().st_size > 10_000
    assert tools.read_file(str(saved), offset=0).ok is True
    saved.unlink()
