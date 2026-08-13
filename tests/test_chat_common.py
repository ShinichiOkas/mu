"""CLI / probe の共通部（層の外）のユニットテスト。

層は表示に無変更・無関知なので、ここで守るのは「**構成と表示が食い違わない**」ことだけ
（合意025 の型）。表示だけの誤りでも、人間が見ている構成と実際に走る構成がずれるなら床が崩れる。
"""

from pathlib import Path

from chat_common import auto_catalog, catalog_roles, skills_paths
from mu.skill_kb import load_skills, unknown_targets

REPO = Path(__file__).resolve().parent.parent


# --- 032: auto モードの装備表示が「効かない」と誤報しない ------------------------
#
# 実発火（032 の実走）: MU_ROLES_DIR=auto ではパッケージ選択が L5 の中で起きるので、
# 起動時点の役割集合は空。そこへ空 dict を渡していたため、`unknown_targets` が
# **全 skill を宛先不明**と報告した——実際には選択後に正しく装着されていた。

def test_catalog_roles_unions_every_package():
    packages, _ = auto_catalog(str(REPO / "roles"))
    names = catalog_roles(packages)
    assert names, "カタログが空（planned 以外のパッケージが無い）"
    # 4ポジション契約はどのパッケージにも居るので、和集合には必ず含まれる
    for position in ("pdm", "pjm", "qa", "implementer"):
        assert position in names, position


def test_catalog_roles_survives_self_contained_duplicates():
    # パッケージは自己完結（026）なので同名役割が複数セットに居る。`load_roles` に
    # 複数パスを渡すと衝突エラーになる——和集合はパッケージごとに読んで束ねる必要がある。
    packages, _ = auto_catalog(str(REPO / "roles"))
    assert len(packages) > 1
    assert "implementer" in catalog_roles(packages)   # 例外を出さずに束ねられる


def test_auto_mode_reports_no_stray_targets_for_the_repo_skills():
    # リポジトリの実データで、auto モードの装備表示が誤報しないこと。
    packages, _ = auto_catalog(str(REPO / "roles"))
    skills = load_skills(*skills_paths())
    assert skills, "skill が1件も無い"
    assert unknown_targets(skills, catalog_roles(packages)) == ()


def test_empty_role_set_would_have_reported_everything():
    # 修理前の挙動を固定しておく（なぜ和集合が要るのかがテストから読める）。
    skills = load_skills(*skills_paths())
    stray = unknown_targets(skills, {})
    assert len(stray) == sum(len(d["applies_to"] or ()) for d in skills.values())
