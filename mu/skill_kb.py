"""skill 定義書（skill knowledge base）の読み込みと装着 — 層の外にある facility（合意029）。

**skill は層ではない。** 層は「1つの落差を埋め、内側を D として使い、その外側に判断を足す」
ものだが、skill が足すのは判断ではなく**知識**である。知識の居場所は既にある——層の外の
データ（`skills/*.md`）と、それを供給する facility（このファイル）。装着点は L4 が
タスクの system を組む1行で、そこは既に役割定義書が着せられている場所と同じ。

**なぜ要るか。** 役割定義書は性質の違う2つを混ぜて運んでいた——ポジションの不変（職掌・
継ぎ目・権限）と、やり方の対策文（入力ファイルは読み取り専用／検査器を自分の成果物に
合わせない）。後者はドメインを跨いで効くので、パッケージが増えるほど手動コピーが膨らむ
（029 起草時の実測: `implementer.md` は5パッケージでバイト同一）。後者を独立の単位に
分離したものが skill である。

**role との違いは3つだけ**:

- **濃度** — 1 task = ちょうど1 role ／ 1 task = 0..N skill
- **宛先** — skill の側が `applies_to` で名乗る。役割定義書は skill を知らない（一方向）
- **権限** — role は持つ ／ **skill は絶対に持たない**（`PERMISSION_KEYS` を名指しで拒否）

宛先を skill 側に置いたのは、目的②（ユーザー側のやり方・プロジェクト方針の記述）が
それを要求するため: `roles/<pkg>/*.md` はリポジトリの共有資産で個々のプロジェクトが
書き換える対象ではなく、かつ 028 で L5 がパッケージを自選する以上、プロジェクト作者は
実行時の役割名を確定できない。確実に名指しできるのは**名前が動かない4ポジション**
（pdm / pjm / qa / implementer）である。副産物として、①の移行は役割定義書から
**削るだけ**になり、実走で調整された文面を触らずに済む。

skill 定義書 1件の形:

    ---
    description: 一行（何のための知識か。将来 PjM に選ばせるときの素性データになる）
    applies_to: implementer, qa     # 省略＝all（明示の `all` も同義）
    maturity: confirmed             # confirmed だけが装着される。draft は載らない
    ---
    本文（やり方。装着時はそのまま連結される——見出しは付けない）

`tools` / `write_scope` は**書けない**。書いてあればエラーで落とす（静かに無視すると、
書いた人には効いているように見えてしまう）。「LLM が出せるのは役割名だけなので権限を
LLM 側から書き換えられない」（合意007 B1）の床は、skill を導入しても不変である。

その他のキー（`origin` / `evidence` / `proposed_by` 等）は文字列のまま持ち回る
（`role_kb.parse_role_doc` と同じ設計）。将来 ③（実走の観測から skill を書き戻す
自己成長の経路）を足すとき、**契約を変えずに**素性を載せられるようにしておくため。
③の安全は maturity の門が持つ——系が書けるのは draft まで、confirmed への昇格は人間
（合意026「verified への昇格は師匠の承認事項」と同型の非対称）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# skill が宣言してはならないキー（絶対ルール。合意029）。権限は role だけが持つ。
PERMISSION_KEYS = ("tools", "write_scope")

# 装着される成熟度。育成中（draft）の文を誤って走りに載せないための門。
ATTACHED_MATURITY = "confirmed"


def _noop(_: Any) -> None:
    pass


def load_skills(*paths: str) -> dict:
    """skill 定義書をディレクトリから読む。引数なし＝ "skills"。

    返り値は `{skill名: {"description", "applies_to", "maturity", "prompt", ...}}`。
    意味論は `role_kb.load_roles` に揃える（特別扱いを作らない）——セットは合成でき、
    存在しないディレクトリは空集合、**同名衝突は両出所を名指しするエラー**（合意025）:

        load_skills()                              # 既定＝同梱の共有ライブラリ
        load_skills("skills", ".mu/skills")        # 共有＋プロジェクト方針（目的②）

    dict の順序＝ロード順（パスの順 × ファイル名順）であり、それが装着時の連結順になる。
    順序を制御したい人間はファイル名で制御できる。
    """
    skills: dict = {}
    origin: dict = {}
    for path in paths or ("skills",):
        p = Path(path)
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.md")):
            if f.stem in skills:
                raise ValueError(
                    f"skill '{f.stem}' が複数のセットで定義されている: "
                    f"{origin[f.stem]} / {path}"
                )
            skills[f.stem] = parse_skill_doc(f.read_text(encoding="utf-8"), origin=str(f))
            origin[f.stem] = path
    return skills


def parse_skill_doc(text: str, origin: str = "") -> dict:
    """skill 定義書を {description, applies_to, maturity, prompt, ...} に分解する。

    `applies_to` は宛先の宣言。**省略も `all` も同じ意味**（＝全役割）で、内部表現は
    どちらも `None` に畳む——書き方は2つ、意味は1つ、見え方は1つ（`equipment_lines` が
    常に `all` として見せる）。省略で書かれたものが人間から見えなくなるのを防ぐ。

    権限キー（`PERMISSION_KEYS`）が現れたら**名指しでエラー**にする。skill は文章だけを
    運ぶ器であり、権限を運ばせると「LLM は自分の権限を書き換えられない」の床が破れる
    ——skill を選ぶ判断が将来 LLM に渡る（合意029 の (b)）ことを見越した設計上の床である。
    """
    doc: dict = {"description": "", "applies_to": None, "maturity": ATTACHED_MATURITY}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                key, _, value = line.partition(":")
                key, value = key.strip().lower(), value.strip()
                if key in PERMISSION_KEYS:
                    raise ValueError(
                        f"skill は権限を宣言できない（合意029 の絶対ルール）: "
                        f"'{key}' が宣言されている{f': {origin}' if origin else ''}。"
                        f"権限（tools / write_scope）を持てるのは役割定義書だけである。"
                    )
                if key == "applies_to":
                    targets = tuple(t.strip() for t in value.split(",") if t.strip())
                    doc["applies_to"] = None if _means_all(targets) else targets
                elif key == "maturity" and value:
                    doc["maturity"] = value.lower()
                elif key and value:
                    doc[key] = value
            body = text[end + 4:].lstrip("\n")
    doc["prompt"] = body.strip()   # 本文は最後に入れる（frontmatter の同名キーに潰させない）
    return doc


def _means_all(targets: tuple) -> bool:
    """宛先の指定が「全役割」を意味するか（省略＝空、または明示の `all`）。"""
    return not targets or any(t.lower() == "all" for t in targets)


def attached_skills(skills: dict, role: str) -> list:
    """その役割に装着される skill 名（ロード順）。

    装着の条件は2つだけ——**宛先が一致すること**（`applies_to` が None＝all か、role を
    名指ししていること）と、**maturity が confirmed であること**。
    """
    return [
        name for name, doc in skills.items()
        if str(doc.get("maturity", "")).lower() == ATTACHED_MATURITY
        and (doc.get("applies_to") is None or role in doc["applies_to"])
    ]


def skill_text(skills: dict, role: str, log: Callable[[Any], None] = _noop) -> str:
    """その役割に装着する本文（ロード順に連結）。装着が無ければ空文字。

    本文は**そのまま連結する**（見出しを付けない）——029 の移行は役割定義書から削って
    移すだけであり、ローダーが文面を飾れば「文言を変えない」が破れる。

    装着したら必ず観測に出す（`("skills", role, [名前], 総文字数)`）。小型モデルでは
    装着量がそのまま劣化要因になるので、合成点で見えるようにしておく
    （skill `observability-at-composition-seams`）。
    """
    names = attached_skills(skills, role)
    if not names:
        return ""
    text = "\n\n".join(skills[n]["prompt"] for n in names)
    log(("skills", role, names, len(text)))
    return text


def unknown_targets(skills: dict, roles: dict) -> tuple:
    """`applies_to` が名指ししている役割のうち、役割セットに居ないものを返す（合意029）。

    `(skill名, 役割名)` の組。**エラーにはしない**——`role_kb.missing_positions` と同じ床で、
    「定義書の無い役割は知識が無い状態で動く」の哲学に揃える。ドメイン役割名を名指しした
    skill は、別パッケージで走れば単に当たらない（それが正常）。ただし黙って消えると
    「書いたのに効かない」が見えないので、呼び出し側が可視化できるようにする。
    """
    return tuple(
        (name, target)
        for name, doc in skills.items()
        for target in (doc.get("applies_to") or ())
        if target not in roles
    )


def equipment_lines(skills: dict) -> str:
    """装備の逆引き一覧（1行＝「- 宛先: skill名, ...」）。装着されるものだけを載せる。

    宛先を skill 側に一本化した代償は「役割定義書を見ても装備が分からない」ことであり、
    それをこの関数が構造で埋める。PjM に見せる一覧と人間に見せる起動表示は**同じ関数**
    から出す（合意025——構成と表示の一致を構造で保証する。`staffing_lines` と同型）。

    省略で書かれた宛先も `all` として見せる（書き方の差を表示に持ち込まない）。
    """
    groups: dict = {}
    for name, doc in skills.items():
        if str(doc.get("maturity", "")).lower() != ATTACHED_MATURITY:
            continue
        for target in doc.get("applies_to") or ("all",):
            groups.setdefault(target, []).append(name)
    lines = [f"- {target}: {', '.join(names)}" for target, names in groups.items()]
    return "\n".join(lines) or "(none)"
