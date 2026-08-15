"""mu/deps.py（依存宣言と決定性の解決）のユニットテスト（合意040）。

守るのは**判断ゼロ**であること。陳腐化の5規則が、追加も削除も内容変更も
コードだけで捕まえる——7走にわたって LLM に判定させて失敗した部分を、規則に置き換える。
"""

import json
from pathlib import Path

from mu.deps import (
    DEPS_FILE, STAMP_FILE, describe, expand, load, load_stamp, parse, save_stamp, stale, stamp,
)


# --- 解析 ---------------------------------------------------------------------

def test_parse_target_prereqs_and_recipe():
    rules = parse("README.md: a.py b.py\n\tREADME を更新する\n")
    assert rules == [{"target": "README.md", "prereqs": ["a.py", "b.py"],
                      "recipe": ["README を更新する"]}]


def test_parse_ignores_comments_and_blank_lines():
    assert parse("# コメント\n\n\nREADME.md: a.py\n")[0]["target"] == "README.md"


def test_parse_supports_line_continuation():
    rules = parse("README.md: a.py \\\n  b.py c.py\n")
    assert rules[0]["prereqs"] == ["a.py", "b.py", "c.py"]


def test_parse_accepts_four_spaces_as_recipe_indent():
    # LLM は TAB を4空白で書くことがある。書式の揺れで recipe を落とさない
    rules = parse("README.md: a.py\n    更新する\n")
    assert rules[0]["recipe"] == ["更新する"]


def test_parse_drops_lines_it_cannot_interpret():
    # 変数・パターンルールは解釈できない。**解釈したふりをしない**
    rules = parse("VAR = x\nREADME.md: a.py\n")
    assert [r["target"] for r in rules] == ["README.md"]


def test_parse_of_empty_text_is_empty():
    assert parse("") == [] and parse(None) == []


# --- 展開 ---------------------------------------------------------------------

def test_expand_resolves_globs_in_stable_order(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mu").mkdir()
    for name in ("l1.py", "l0.py"):
        (tmp_path / "mu" / name).write_text("x", encoding="utf-8")
    assert expand(["mu/*.py"], ".") == ["mu/l0.py", "mu/l1.py"]


def test_expand_keeps_a_literal_prereq_even_when_missing(tmp_path, monkeypatch):
    # 実在しない前提は判定材料。黙って消すと「削除」を見逃す
    monkeypatch.chdir(tmp_path)
    assert expand(["gone.py"], ".") == ["gone.py"]


def test_expand_dedupes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    assert expand(["a.py", "*.py"], ".") == ["a.py"]


# --- 陳腐化の5規則 -------------------------------------------------------------

def _repo(tmp_path):
    (tmp_path / "mu").mkdir()
    (tmp_path / "mu" / "l0.py").write_text("v1", encoding="utf-8")
    (tmp_path / "README.md").write_text("doc", encoding="utf-8")
    return [{"target": "README.md", "prereqs": ["mu/*.py"], "recipe": []}]


def test_stale_when_target_is_missing(tmp_path):
    rules = _repo(tmp_path)
    (tmp_path / "README.md").unlink()
    marks = stamp(rules, str(tmp_path))
    assert [s["target"] for s in stale(rules, str(tmp_path), marks)] == ["README.md"]


def test_stale_when_there_is_no_previous_record(tmp_path):
    # 初回は保守的に「陳腐化」とする（安全側）
    rules = _repo(tmp_path)
    items = stale(rules, str(tmp_path), {})
    assert items and "前回の記録が無い" in items[0]["reasons"]


def test_fresh_when_nothing_changed(tmp_path):
    # **これが no_action の根拠。判断は1つも要らない**
    rules = _repo(tmp_path)
    marks = stamp(rules, str(tmp_path))
    assert stale(rules, str(tmp_path), marks) == []


def test_stale_when_a_prereq_changed(tmp_path):
    rules = _repo(tmp_path)
    marks = stamp(rules, str(tmp_path))
    (tmp_path / "mu" / "l0.py").write_text("v2", encoding="utf-8")
    items = stale(rules, str(tmp_path), marks)
    assert items and "mu/l0.py が変わった" in items[0]["reasons"]


def test_stale_when_a_prereq_was_deleted(tmp_path):
    # 032 R2 型のドリフト（probe_research.py の削除）
    rules = _repo(tmp_path)
    marks = stamp(rules, str(tmp_path))
    (tmp_path / "mu" / "l0.py").unlink()
    items = stale(rules, str(tmp_path), marks)
    assert items and "mu/l0.py が消えた" in items[0]["reasons"]


def test_stale_when_a_prereq_was_added(tmp_path):
    # 032 R1 型のドリフト（skill の追加）——glob に新しく合致したもの
    rules = _repo(tmp_path)
    marks = stamp(rules, str(tmp_path))
    (tmp_path / "mu" / "l1.py").write_text("new", encoding="utf-8")
    items = stale(rules, str(tmp_path), marks)
    assert items and "mu/l1.py が増えた" in items[0]["reasons"]


def test_stale_reports_only_the_affected_target(tmp_path):
    rules = _repo(tmp_path)
    (tmp_path / "notes.md").write_text("n", encoding="utf-8")
    (tmp_path / "other.txt").write_text("o", encoding="utf-8")
    rules.append({"target": "notes.md", "prereqs": ["other.txt"], "recipe": []})
    marks = stamp(rules, str(tmp_path))
    (tmp_path / "mu" / "l0.py").write_text("v2", encoding="utf-8")
    assert [s["target"] for s in stale(rules, str(tmp_path), marks)] == ["README.md"]


# --- 入出力 -------------------------------------------------------------------

def test_load_returns_none_without_a_declaration(tmp_path):
    # 宣言が無ければこの機構は働かない（既存の挙動を1ミリも変えない）
    assert load(str(tmp_path)) is None


def test_load_reads_the_declaration(tmp_path):
    (tmp_path / DEPS_FILE).write_text("README.md: a.py\n", encoding="utf-8")
    assert load(str(tmp_path))[0]["target"] == "README.md"


def test_stamp_round_trip(tmp_path):
    rules = _repo(tmp_path)
    marks = stamp(rules, str(tmp_path))
    save_stamp(marks, str(tmp_path))
    assert load_stamp(str(tmp_path)) == marks
    assert json.loads((tmp_path / STAMP_FILE).read_text(encoding="utf-8")) == marks


def test_load_stamp_survives_a_broken_file(tmp_path):
    (tmp_path / STAMP_FILE).write_text("{壊れている", encoding="utf-8")
    assert load_stamp(str(tmp_path)) == {}      # 壊れていたら「記録なし」＝安全側（走る）


def test_describe_puts_the_reason_next_to_the_target():
    text = describe([{"target": "README.md", "reasons": ["a.py が変わった"]}])
    assert "README.md" in text and "a.py が変わった" in text


# --- 040 v2: 書式の是正（師匠の指示「glob 必須にする」） -------------------------
#
# 047 の実測: gemma4 は 58 ファイルを1つずつ列挙し、**追加を構造的に見逃した**。
# 列挙は「いま在るもの」しか捕まえない。畳む方向は安全側（前提が増える＝余計に走るだけ）。

from mu.deps import fold_globs, normalize                      # noqa: E402


def test_fold_turns_an_enumeration_into_a_glob():
    prereqs = ["mu/l0.py", "mu/l1.py", "mu/l2.py"]
    folded, notes = fold_globs(prereqs)
    assert folded == ["mu/*.py"]
    assert notes == ["列挙 3 件を mu/*.py に畳んだ"]


def test_fold_handles_the_repository_root():
    folded, _ = fold_globs(["tools.py", "chat_common.py"])
    assert folded == ["*.py"]


def test_fold_keeps_a_lone_file_literal():
    # 1件だけの指定は意図的な選択とみなす（畳むと意図を壊す）
    folded, notes = fold_globs(["pyproject.toml", "mu/l0.py", "mu/l1.py"])
    assert set(folded) == {"pyproject.toml", "mu/*.py"} and len(notes) == 1


def test_fold_leaves_existing_globs_alone():
    folded, notes = fold_globs(["mu/*.py", "roles/*.md"])
    assert folded == ["mu/*.py", "roles/*.md"] and notes == []


def test_fold_groups_by_extension_not_just_directory():
    folded, _ = fold_globs(["roles/coding/pdm.md", "roles/coding/qa.md",
                            "roles/coding/manifest.json"])
    assert "roles/coding/*.md" in folded and "roles/coding/manifest.json" in folded


def test_normalize_drops_self_references():
    # gemma4 は DEPS.mk 自身を前提に含めた——書き換えるたびに陳腐化する永久の罠
    rules = [{"target": "README.md", "prereqs": ["DEPS.mk", ".mu-stamp.json", "README.md",
                                                 "mu/l0.py", "mu/l1.py"], "recipe": []}]
    out, notes = normalize(rules)
    assert out[0]["prereqs"] == ["mu/*.py"]
    assert any("自己参照を落とした" in n for n in notes)


def test_normalize_reports_every_change_it_makes():
    # 宣言は人間がレビューする前提のもの。**黙って書き換えたら読めなくなる**
    rules = [{"target": "README.md", "prereqs": ["a.py", "b.py"], "recipe": []}]
    _, notes = normalize(rules)
    assert notes and all(n.startswith("README.md: ") for n in notes)


def test_folding_makes_an_addition_detectable(tmp_path):
    # **これが 047 の見逃しへの対処**。列挙のままなら新しいファイルは永久に見えない
    (tmp_path / "mu").mkdir()
    (tmp_path / "mu" / "l0.py").write_text("v1", encoding="utf-8")
    (tmp_path / "mu" / "l1.py").write_text("v1", encoding="utf-8")
    (tmp_path / "README.md").write_text("doc", encoding="utf-8")
    listed = [{"target": "README.md", "prereqs": ["mu/l0.py", "mu/l1.py"], "recipe": []}]

    marks_listed = stamp(listed, str(tmp_path))
    folded, _ = normalize(listed)
    marks_folded = stamp(folded, str(tmp_path))
    (tmp_path / "mu" / "l2.py").write_text("new", encoding="utf-8")     # 追加ドリフト

    assert stale(listed, str(tmp_path), marks_listed) == []            # 列挙は**見逃す**
    assert stale(folded, str(tmp_path), marks_folded)                  # glob は捕まえる
