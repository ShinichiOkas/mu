"""skill 定義書（skill knowledge base）の facility のユニットテスト（合意029）。

skill は**層ではない**——層の外のデータ（`skills/*.md`）＋ facility（`mu/skill_kb.py`）であり、
役割定義書から「やり方」を独立した単位に分離したもの。role との違いは3つだけ:

- **濃度**: 1 task = 1 role ／ 1 task = 0..N skill
- **宛先**: skill の側が `applies_to` で名乗る（役割定義書は skill を知らない）
- **権限**: role は持つ ／ **skill は絶対に持たない**（コードが名指しで拒否する）
"""

import pytest

from mu.skill_kb import (
    attached_skills, equipment_lines, load_skills, parse_skill_doc, skill_text, unknown_targets,
)


def write(d, name, text):
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(text, encoding="utf-8")
    return d


def doc(body="本文", **frontmatter):
    lines = "\n".join(f"{k}: {v}" for k, v in frontmatter.items())
    return f"---\n{lines}\n---\n\n{body}\n" if lines else f"{body}\n"


def logger():
    events = []
    return events, events.append


# --- パース: frontmatter と本文 -------------------------------------------------

def test_skill_doc_parses_frontmatter_and_body():
    d = parse_skill_doc("---\ndescription: 一行\napplies_to: implementer, qa\n"
                        "maturity: confirmed\n---\n\n本文である\n")
    assert d["description"] == "一行"
    assert d["applies_to"] == ("implementer", "qa")
    assert d["maturity"] == "confirmed"
    assert d["prompt"] == "本文である"


def test_body_is_kept_verbatim_without_the_frontmatter():
    # 移行（029 フェーズ B）は「役割定義書から削って skill に移す」だけ。本文に手を入れない
    # 以上、ローダーが本文を飾ってはならない（見出しの付与もしない）。
    body = "- **入力ファイルは読み取り専用**。仕様・設計が入力として挙げるファイルを上書きしない。"
    assert parse_skill_doc(f"---\ndescription: x\n---\n\n{body}\n")["prompt"] == body


# --- 宛先: applies_to（省略＝all、明示の all も同義） ----------------------------

def test_applies_to_all_and_omission_mean_the_same():
    assert parse_skill_doc(doc(description="x", applies_to="all"))["applies_to"] is None
    assert parse_skill_doc(doc(description="x"))["applies_to"] is None


def test_a_skill_without_a_target_attaches_to_every_role(tmp_path):
    write(tmp_path, "everywhere", doc("ALL-MARKER", description="全員に効く"))
    skills = load_skills(str(tmp_path))
    for role in ("implementer", "qa", "pdm", "writer"):
        assert attached_skills(skills, role) == ["everywhere"]


def test_a_skill_attaches_only_to_the_role_it_names(tmp_path):
    write(tmp_path, "impl-only", doc("IMPL-MARKER", description="x", applies_to="implementer"))
    skills = load_skills(str(tmp_path))
    assert attached_skills(skills, "implementer") == ["impl-only"]
    assert attached_skills(skills, "qa") == []


def test_a_skill_can_name_several_roles(tmp_path):
    write(tmp_path, "shared", doc("S", description="x", applies_to="implementer, qa"))
    skills = load_skills(str(tmp_path))
    assert attached_skills(skills, "qa") == ["shared"]
    assert attached_skills(skills, "architect") == []


def test_positions_of_the_four_contract_are_targetable(tmp_path):
    # 028 でパッケージが自動選択される以上、プロジェクト側 skill（目的②）が確実に
    # 名指しできるのは**名前が動かない4ポジション**だけ。ここが外れると ② が成立しない。
    write(tmp_path, "spec-style", doc("PDM-MARKER", description="x", applies_to="pdm"))
    skills = load_skills(str(tmp_path))
    assert attached_skills(skills, "pdm") == ["spec-style"]
    assert attached_skills(skills, "implementer") == []


# --- maturity の門 --------------------------------------------------------------

def test_draft_skill_is_not_attached(tmp_path):
    write(tmp_path, "half-baked", doc("DRAFT-MARKER", description="x", maturity="draft"))
    skills = load_skills(str(tmp_path))
    assert "half-baked" in skills                      # ロードはされる（見える）
    assert attached_skills(skills, "implementer") == []   # が、走りには載らない


def test_maturity_defaults_to_confirmed(tmp_path):
    # 門は opt-out（029 実行時の判断）: 育成中のものは書き手が draft と明示する。
    # ③（系が skill を書き戻す）を作るときは、書き手側が draft を明示するのが契約。
    write(tmp_path, "plain", doc("P", description="x"))
    assert load_skills(str(tmp_path))["plain"]["maturity"] == "confirmed"
    assert attached_skills(load_skills(str(tmp_path)), "qa") == ["plain"]


# --- 絶対ルール: skill は権限を持たない ------------------------------------------

@pytest.mark.parametrize("key, value", [("tools", "read_file, write_file"), ("write_scope", "any")])
def test_permission_keys_are_rejected_by_name(key, value):
    # 静かに無視したら、書いた人には効いているように見えてしまう（025 で取り除いた不透明さと同種）。
    # 「LLM が出せるのは役割名だけ→権限を書き換えられない」（007 B1）の床は skill 導入後も不変。
    with pytest.raises(ValueError) as e:
        parse_skill_doc(f"---\n{key}: {value}\n---\n\n本文\n", origin="skills/bad.md")
    assert key in str(e.value) and "skills/bad.md" in str(e.value)


def test_permission_keys_are_rejected_through_the_loader(tmp_path):
    write(tmp_path, "sneaky", "---\ntools: execute_command\n---\n\n本文\n")
    with pytest.raises(ValueError) as e:
        load_skills(str(tmp_path))
    assert "tools" in str(e.value) and "sneaky" in str(e.value)


# --- ③を塞がない: 未知のキーは持ち回る ------------------------------------------

def test_unknown_frontmatter_keys_survive_the_loader(tmp_path):
    # origin / evidence / proposed_by を**契約変更なしに**後から足せるようにしておく
    # （role_kb.parse_role_doc と同じ設計）。③の器はこれだけで足りる。
    write(tmp_path, "learned", doc("L", description="x", origin="observed",
                                   evidence="runs/2026-08-12-029/r1.log"))
    s = load_skills(str(tmp_path))["learned"]
    assert s["origin"] == "observed" and s["evidence"] == "runs/2026-08-12-029/r1.log"


# --- ロードと合成（roles と同じ意味論に揃える） ----------------------------------

def test_missing_directory_is_an_empty_set(tmp_path):
    assert load_skills(str(tmp_path / "nope")) == {}


def test_sets_compose_and_duplicate_names_name_both_origins(tmp_path):
    shared, project = tmp_path / "shared", tmp_path / "project"
    write(shared, "a", doc("A", description="x"))
    write(project, "b", doc("B", description="x"))
    assert sorted(load_skills(str(shared), str(project))) == ["a", "b"]

    write(project, "a", doc("A2", description="x"))
    with pytest.raises(ValueError) as e:
        load_skills(str(shared), str(project))
    assert str(shared) in str(e.value) and str(project) in str(e.value)


# --- 宛先の不一致は可視化する（missing_positions と同型の床） ---------------------

def test_unknown_targets_reports_names_absent_from_the_role_set(tmp_path):
    # ドメイン役割名も書けるが、当たらなければ**エラーにせず可視化**する
    # ——「定義書の無い役割は知識が無い状態で動く」の哲学と同じ扱い。
    write(tmp_path, "novel", doc("N", description="x", applies_to="illustrator"))
    write(tmp_path, "fine", doc("F", description="x", applies_to="qa"))
    skills = load_skills(str(tmp_path))
    assert unknown_targets(skills, {"qa": {}, "implementer": {}}) == (("novel", "illustrator"),)
    assert unknown_targets(skills, {"qa": {}, "illustrator": {}}) == ()


# --- 装着テキストと観測 ----------------------------------------------------------

def test_skill_text_joins_the_bodies_in_load_order(tmp_path):
    write(tmp_path, "b-second", doc("SECOND", description="x", applies_to="implementer"))
    write(tmp_path, "a-first", doc("FIRST", description="x", applies_to="implementer"))
    text = skill_text(load_skills(str(tmp_path)), "implementer")
    assert text == "FIRST\n\nSECOND"      # ファイル名順＝人間が順序を制御できる


def test_attachment_is_logged_with_names_and_size(tmp_path):
    # 小型モデルでは装着量がそのまま劣化要因。合成点で観測に出す
    # （observability-at-composition-seams）。
    write(tmp_path, "one", doc("12345", description="x", applies_to="qa"))
    events, log = logger()
    text = skill_text(load_skills(str(tmp_path)), "qa", log=log)
    assert ("skills", "qa", ["one"], len(text)) in events


def test_nothing_attached_produces_no_text_and_no_event(tmp_path):
    write(tmp_path, "one", doc("X", description="x", applies_to="qa"))
    events, log = logger()
    assert skill_text(load_skills(str(tmp_path)), "implementer", log=log) == ""
    assert events == []


# --- 逆引きの表示（構成と表示の一致を構造で保証する。025 の型） -------------------

def test_equipment_lines_show_the_reverse_lookup_with_all_normalized(tmp_path):
    write(tmp_path, "everywhere", doc("A", description="x"))               # 省略
    write(tmp_path, "impl-rule", doc("B", description="x", applies_to="implementer"))
    write(tmp_path, "draft-one", doc("C", description="x", maturity="draft"))
    lines = equipment_lines(load_skills(str(tmp_path)))
    assert "- all: everywhere" in lines            # 省略も `all` として見える
    assert "- implementer: impl-rule" in lines
    assert "draft-one" not in lines                # 装着されないものは装備一覧に出さない


def test_equipment_lines_say_none_when_empty():
    assert equipment_lines({}) == "(none)"
