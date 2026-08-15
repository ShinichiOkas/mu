"""依存宣言（Makefile 形式）と決定性の解決 — 層の外にある facility（合意040）。

師匠の設計:

    依存性記述があった場合、その依存性を紐解いて何を変更すべきかは決定性のツールで判断し、
    その結果に従ってLLMが動く構造の方が確実で柔軟である。
    **Makefile形式は依存を決めるが手順を決めないから。**

**判断の難易度を、形式の選択で下げる。** 「README は実装と一致しているか」は難しく、
検査器を書かせると盲点が入った（040: 実在ファイルを嘘と誤報して11件／042: skill を1行も見ずに0件。
7走とも失敗）。「README は何に依存するか」は易しく、しかも**人間が一目でレビューできる**。

`make` は呼ばない。**形式だけ借りる**——LLM が熟知していること・人間が読めることが利益であり、
陳腐化の判定はハッシュ比較で足りる（`workspace.digest()`）。Windows に make は無く、
recipe がシェル前提だと「LLM が直す」を書けない。

書式（Makefile の部分集合）:

    # コメント
    README.md: mu/*.py roles/*.md skills/*.md
    <TAB>README.md を依存先の変更に合わせて更新する

    target: prereq...    前提は glob 可。`\\` による行継続に対応
    <TAB>recipe          自然言語のタスク（このスプリントでは実行しない。合意040 スコープ外）

**失敗の向きは安全側**である——依存を広く書けば余計に走るだけ（偽陽性）。
書き漏らせば見逃すが、宣言は1行なので人間が読んで気づける。
"""

from __future__ import annotations

import json
from pathlib import Path

from .workspace import digest

DEPS_FILE = "DEPS.mk"
STAMP_FILE = ".mu-stamp.json"


def parse(text: str) -> list[dict]:
    """Makefile 形式の依存宣言を規則の列にする。

    返すのは `{"target": str, "prereqs": [str], "recipe": [str]}` の列。
    未知の書式（変数・パターンルール・条件分岐）は**黙って無視せず落とす**——
    解釈できないものを解釈したふりをしない（合意040 の床）。
    """
    rules: list[dict] = []
    pending = ""
    for raw in (text or "").splitlines():
        line = raw.rstrip("\n")
        if pending:                                   # 行継続の途中
            line = pending + " " + line.strip()
            pending = ""
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("\t") or line.startswith("    "):
            if rules:                                 # recipe 行（TAB か4空白）
                rules[-1]["recipe"].append(stripped)
            continue
        if stripped.endswith("\\"):                   # 行継続
            pending = stripped[:-1].rstrip()
            continue
        if ":" not in stripped:
            continue
        target, _, prereq_text = stripped.partition(":")
        target = target.strip()
        if not target:
            continue
        rules.append({
            "target": target,
            "prereqs": [p for p in prereq_text.split() if p],
            "recipe": [],
        })
    return rules


def expand(prereqs, root: str = ".") -> list[str]:
    """前提の glob を実ファイルに展開する（順序は安定・重複は除く）。

    glob に合致するものが無ければ、その pattern は**そのまま残す**——
    「実在しない前提」は陳腐化の判定材料であり、黙って消すと削除を見逃す。
    """
    base = Path(root)
    out: list[str] = []
    for p in prereqs:
        if any(ch in p for ch in "*?["):
            hits = sorted(str(q.relative_to(base)).replace("\\", "/")
                          for q in base.glob(p) if q.is_file())
            out.extend(hits or [])
        else:
            out.append(p)
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def stamp(rules: list[dict], root: str = ".") -> dict:
    """いまの前提のハッシュ表を作る（ターゲットごと）。走を跨ぐ記憶はこれ1つ。"""
    base = Path(root)
    out: dict = {}
    for rule in rules:
        marks: dict = {}
        for p in expand(rule["prereqs"], root):
            d = digest(base / p)
            if d:
                marks[p] = d
        out[rule["target"]] = marks
    return out


def stale(rules: list[dict], root: str = ".", marks: dict | None = None) -> list[dict]:
    """**陳腐化したターゲット**を返す（判断ゼロ）。

    5つの規則はすべて決定性で、追加も削除も捕まえる:

      1. ターゲットが存在しない                       → 陳腐化（新規作成）
      2. stamp にターゲットの記録が無い               → 陳腐化（初回・保守的）
      3. 前提のハッシュが stamp と違う                 → 陳腐化（内容の変更）
      4. stamp にあった前提が消えている                → 陳腐化（**削除**）
      5. glob に新しく合致する前提が増えた             → 陳腐化（**追加**）

    返り値の各要素は `{"target", "reasons": [str]}`——**なぜ動くのかが証跡として残る**。
    """
    base = Path(root)
    marks = marks or {}
    out: list[dict] = []
    for rule in rules:
        target = rule["target"]
        reasons: list[str] = []
        if not (base / target).is_file():
            reasons.append(f"{target} が無い")
        previous = marks.get(target)
        if previous is None:
            reasons.append("前回の記録が無い")
        current = {p: digest(base / p) for p in expand(rule["prereqs"], root)}
        current = {p: d for p, d in current.items() if d}
        if previous is not None:
            for p, d in current.items():
                if p not in previous:
                    reasons.append(f"{p} が増えた")
                elif previous[p] != d:
                    reasons.append(f"{p} が変わった")
            for p in previous:
                if p not in current:
                    reasons.append(f"{p} が消えた")
        if reasons:
            out.append({"target": target, "reasons": reasons})
    return out


def load(root: str = ".") -> list[dict] | None:
    """作業ディレクトリの依存宣言を読む。**無ければ None**（＝この機構は働かない）。"""
    p = Path(root) / DEPS_FILE
    if not p.is_file():
        return None
    return parse(p.read_text(encoding="utf-8", errors="replace"))


def load_stamp(root: str = ".") -> dict:
    p = Path(root) / STAMP_FILE
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_stamp(marks: dict, root: str = ".") -> None:
    """**成功した走だけ**が呼ぶ。失敗した走で更新すると、直っていないものを新しいと記録する。"""
    (Path(root) / STAMP_FILE).write_text(
        json.dumps(marks, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def describe(items: list[dict]) -> str:
    """陳腐化の一覧を、目的に添える1文にする（LLM に渡す事実）。"""
    return "\n".join(
        f"- {it['target']}（{', '.join(it['reasons'][:4])}）" for it in items)
