"""役割定義書（role knowledge base）の読み込みと適用 — 層の外にある facility。

L4 は「そこに役割が居る」ことだけを知り、**どういう役割か**はここが供給する（合意008）。
この分離の要点は、**定義書の"形"だけが契約であり、"出所"は差し替え可能**なこと——
いまはリポジトリの `roles/*.md` を読むが、将来 DB・API・別リポジトリに移しても、
同じ形の dict を返す loader を用意すれば L4 は無変更で動く。

**役割集合は開いている**（合意024）。コードが名前を知るポジションは4つだけ——
`pdm` / `pjm`（L4/L5 の内部ポジション。人選対象外）、`qa`（プロセス末尾に必ず立つ
独立検証）、`implementer`（未知の役割名のフォールバック先）——で、それ以外の役割は
純粋なデータ。対応するドメインが増えるごとに定義書を**足していく**（小説なら
編集者・執筆者・挿絵師が登場する）。どの役割を使うか（人選）は PjM の仕事であり、
コードは関知しない。

役割定義書 1件の形:

    {"prompt": 本文, "tools": [許可ツール名]|None, "write_scope": "own"|"any", ...}

- `prompt` は**やり方**（知識・規範）。無ければ「役割は認識しているが知識が無い」状態になる
  ——それは異常ではなく、多くの場合その仕事は失敗する。安全網で埋めない。
- `tools` / `write_scope` は**権限の宣言**。適用するのはコード（`role_tools`）であり、
  LLM が出せるのは役割名だけなので、権限は LLM 側から書き換えられない（合意007 B1）。
- その他のキーは、コード側のミニマム定義を上書きする値として持ち回る（合意008。例: qa の file）。
- 本文は `## <節>` で仕事ごとに分けられる（PdM の specify / respecify 等）。節は
  ミニマム定義の上書き値の置き場にもなる（例: `## spec-artifact`）。
"""

from __future__ import annotations

import re
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Sequence

from .l1 import Tool, ToolResult

# L4 の内部ポジション（PdM/PjM）。作業タスクに割り当てる役割ではないので人選対象から外す。
L4_ROLES = ("pdm", "pjm")

# コードが名前を知る4ポジション（合意024 の契約）。これ以外の役割は純粋なデータ。
POSITIONS = (*L4_ROLES, "qa", "implementer")


def load_roles(*paths: str) -> dict:
    """role 定義書（PjM のナレッジベース）をディレクトリから読む。引数なし＝ "roles"。

    返り値は `{role名: {"prompt": 本文, "tools": [...]|None, "write_scope": "own"|"any"}}`。
    **この dict が人選の範囲そのもの**（合意025）——PjM はここに載る役割からしか選べない。
    「この範囲で選んでほしい」の意思表示は、どのセット（ディレクトリ）をロードするかで行う:

        load_roles()                          # 既定の roles/ 一式
        load_roles("roles", "roles-novel")    # セットの合成（役割はドメインごとに足していく）

    合成時の床: **同名役割の衝突はエラー**（静かな上書きはしない。両方の出所を名指しする）。
    存在しないディレクトリは空集合として扱う（定義書が無い役割は「知識が無い状態」で動く
    ——その不足は `missing_positions` で可視化する）。

    合意007 B1: 役割の**権限**も役割定義に属するデータとし、frontmatter で宣言する:

        ---
        tools: read_file, list_dir, execute_command, write_file   # 省略＝全ツール
        write_scope: own                                          # own＝自タスクの出力のみ
        ---

    権限を適用するのはコード（`role_tools`）であり、PjM が出せるのは role 名だけ——
    **PjM/LLM は自分の権限を書き換えられない**。人間は roles/*.md を直接直せる。
    """
    roles: dict = {}
    origin: dict = {}
    for path in paths or ("roles",):
        p = Path(path)
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.md")):
            if f.stem in roles:
                raise ValueError(
                    f"役割 '{f.stem}' が複数のセットで定義されている: "
                    f"{origin[f.stem]} / {path}"
                )
            roles[f.stem] = parse_role_doc(f.read_text(encoding="utf-8"))
            origin[f.stem] = path
    return roles


def missing_positions(roles: dict) -> tuple:
    """4ポジション（POSITIONS）のうち定義書が無いものを返す（全部あれば空。合意025）。

    エラーにはしない——「定義書が無ければ知識ゼロで動いて失敗する。それが正しい挙動」
    の哲学のまま、不足を呼び出し側に**見える**ようにするだけの床。
    """
    return tuple(name for name in POSITIONS if name not in roles)


def parse_role_doc(text: str) -> dict:
    """role 定義書を {prompt, tools, write_scope, ...} に分解する（frontmatter は本文に混ぜない）。

    tools / write_scope 以外のキーも文字列のまま持ち回る——コード側のミニマム定義を
    上書きする値（例: qa の task/file/criterion）の経路であり、捨てると
    「frontmatter で上書きできる」の契約（合意008）が不通になる（023 A1 で実発火）。
    """
    doc: dict = {"tools": None, "write_scope": "any"}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                key, _, value = line.partition(":")
                key, value = key.strip().lower(), value.strip()
                if key == "tools":
                    doc["tools"] = [t.strip() for t in value.split(",") if t.strip()]
                elif key == "write_scope" and value:
                    doc["write_scope"] = value.lower()
                elif key and value:
                    doc[key] = value
            body = text[end + 4:].lstrip("\n")
    doc["prompt"] = body   # 本文は最後に入れる（frontmatter の同名キーに潰させない）
    return doc


def task_roles(roles: dict) -> dict:
    """人選・タスク割当の対象になる役割（＝作業する役割）。L4 のポジションは除く（合意008）。"""
    return {name: doc for name, doc in roles.items() if name not in L4_ROLES}


def staffing_lines(roles: dict) -> str:
    """人選対象の役割一覧（1行＝「- 名前: 職掌の1行目」）。

    PjM の process プロンプトに載る一覧と、CLI が人間に見せる一覧を**同じ関数**から
    出す（合意025——構成と表示の一致を構造で保証する）。pjm.md は「listed role names
    だけを使え」と言う——見せる範囲は人選の検証（task_roles）と一致していなければ
    ならず、L4 のポジション（pdm/pjm）は人選できないので載せない。
    """
    lines = [f"- {name}: {_first_line(role_prompt(doc))}"
             for name, doc in task_roles(roles).items()]
    return "\n".join(lines) or "(none)"


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip().lstrip("# ")
    return ""


def role_prompt(doc: Any, section: str | None = None) -> str:
    """role 定義の本文。旧形式（素の文字列）も受ける。

    `section` を渡すと「前文＋`## <section>` の節」を返す（合意008）。1つの役割が複数の仕事を
    持つとき（PdM の specify / respecify、PjM の process / decide）に、共通の前文を保ったまま
    その仕事の指示だけを取り出すため。節が無ければ本文全体を返す。
    """
    text = doc if isinstance(doc, str) else str((doc or {}).get("prompt", ""))
    if not section or not text:
        return text
    body = role_section(doc, section)
    if body is None:
        return text
    preamble = re.split(r"^##\s+\S+\s*$", text, flags=re.M)[0].strip()
    return f"{preamble}\n\n{body}".strip()


def role_section(doc: Any, section: str) -> str | None:
    """役割定義書の `## <section>` の本文だけを返す（無ければ None）。

    節は「その役割の1つの仕事」の単位。コードのミニマム定義を上書きする値の置き場にもなる
    （例: `## spec-artifact` が SPEC.md の注記を上書きする・合意008）。
    """
    text = doc if isinstance(doc, str) else str((doc or {}).get("prompt", ""))
    parts = re.split(r"^##\s+(\S+)\s*$", text, flags=re.M)
    for name, body in zip(parts[1::2], parts[2::2]):
        if name.strip().lower() == section.lower():
            return body.strip()
    return None


def role_perms(doc: Any) -> tuple[list | None, str]:
    """role 定義の権限（許可ツール, 書き込み範囲）。宣言が無ければ無制限。"""
    if isinstance(doc, dict):
        return doc.get("tools"), str(doc.get("write_scope") or "any").lower()
    return None, "any"


def role_tools(
    tools: Sequence[Tool], doc: Any, own_file: str, role: str, log: Callable
) -> list:
    """役割の権限でツール群を絞る（合意007 B1）。

    f1×12b の観測: QA が成果物を自分で修正してから合格判定した（自己修正→自己承認）。
    role プロンプトの「実装しない」は確率的にしか効かない。塞ぐのは**役割の職掌違反**であって
    能力ではない（決めたこと4）——実装者は制限せず、QA だけが自分の判定書に閉じる。
    拒否・非配布はログに出す（塞ぐが観測は殺さない）。
    """
    allow, scope = role_perms(doc)
    out = []
    for func, usage in tools:
        name = func.__name__
        if allow is not None and name not in allow:
            log(("tool_withheld", role, name))
            continue
        if scope == "own" and name in ("write_file", "edit_file"):
            func = _own_file_only(func, own_file, role, log)
            usage = f"{usage} ※このタスクで書き換えてよいのは {own_file} のみ"
        out.append((func, usage))
    return out


def _own_file_only(func: Callable, own_file: str, role: str, log: Callable) -> Callable:
    """書き込み系ツールを「自タスクの出力ファイルのみ」に閉じる包み（拒否は steering で返す）。"""
    @wraps(func)
    def guarded(path: str, *args, **kwargs):
        if Path(path).resolve() != Path(own_file).resolve():
            log(("permission_denied", role, func.__name__, path))
            return ToolResult(
                f"error: 役割 '{role}' が書き換えてよいのは {own_file} だけである"
                f"（{path} への書き込みは権限で禁止）。成果物を自分で直してはならない——"
                "問題は自分の出力ファイルに事実として記述すること。",
                ok=False,
                facts={"action": func.__name__, "path": path, "denied": True, "role": role},
            )
        return func(path, *args, **kwargs)

    return guarded
