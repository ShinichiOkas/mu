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


def fold_globs(prereqs) -> tuple[list[str], list[str]]:
    """**列挙を glob に畳む**（合意040 v2・師匠の指示「書式を glob 必須にする」）。

    同じディレクトリ・同じ拡張子のリテラルが2つ以上あれば `dir/*.ext` に置き換える。
    返り値は (畳んだ前提, 実況に出す注記)。

    **Why**: 列挙は「いま在るもの」しか捕まえず、**追加に構造的に弱い**。
    047 の実測——gemma4 は 58 ファイルを1つずつ列挙し、R1 のドリフト（skill の追加）を
    見逃した。glob なら合致するものが増えた時点で陳腐化する。
    畳む方向は**安全側**である（前提が増える＝余計に走るだけで、見逃しは増えない）。

    畳んだことは**必ず注記に出す**——宣言は人間がレビューする前提のものなので、
    コードが黙って書き換えたら読めなくなる。
    """
    groups: dict = {}
    literals, patterns = [], []
    for p in prereqs:
        (patterns if any(ch in p for ch in "*?[") else literals).append(p)
    for p in literals:
        path = Path(p)
        if not path.suffix:
            continue
        groups.setdefault((path.parent.as_posix(), path.suffix), []).append(p)
    folded, notes, absorbed = list(patterns), [], set()
    for (parent, suffix), members in sorted(groups.items()):
        if len(members) < 2:
            continue
        pattern = f"*{suffix}" if parent in (".", "") else f"{parent}/*{suffix}"
        folded.append(pattern)
        absorbed.update(members)
        notes.append(f"列挙 {len(members)} 件を {pattern} に畳んだ")
    folded.extend(p for p in literals if p not in absorbed)
    seen, uniq = set(), []
    for p in folded:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq, notes


def normalize(rules: list[dict]) -> tuple[list[dict], list[str]]:
    """宣言を解決に使える形に整える。返り値は (規則, 注記)。

    2つだけ行う。どちらも**書式の是正**であって、依存の内容には踏み込まない:

    1. **列挙を glob に畳む**（追加への弱さを消す）
    2. **自己参照を落とす**——ターゲット自身・`DEPS.mk`・刻印ファイルを前提から除く。
       047 で gemma4 は `DEPS.mk` を自分の前提に含めた。宣言を書き換えるたびに
       ハッシュが変わるので、**永久に陳腐化し続ける罠**になる
    """
    out, notes = [], []
    for rule in rules:
        drop = {rule["target"], DEPS_FILE, STAMP_FILE}
        kept = [p for p in rule["prereqs"] if p not in drop]
        if len(kept) != len(rule["prereqs"]):
            notes.append(f"{rule['target']}: 自己参照を落とした"
                         f"（{', '.join(sorted(set(rule['prereqs']) & drop))}）")
        folded, fold_notes = fold_globs(kept)
        notes.extend(f"{rule['target']}: {n}" for n in fold_notes)
        out.append({**rule, "prereqs": folded})
    return out, notes


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


def uncovered(rules: list[dict], root: str = ".", limit: int = 6) -> list[dict]:
    """宣言が**どの前提にも合致しないファイル**を、置き場所ごとに数える（合意040 v2）。

    **警告だけで、止めない。** 「宣言していないものは全部依存」にすると宣言の意義が消える
    （ターゲット自身も生成物も巻き込む）。ここでやるのは、**見逃しを静かでなくする**ことだけ。

    **Why**: 047 の実測——gemma4 の宣言は `skills/` に一度も触れておらず、
    skill の追加を永久に見逃した。書式（glob）を是正しても、**宣言に無いディレクトリは
    現れない**。穴の正体は書式ではなく網羅であり、網羅は機械的に測れる
    （gemma4 の宣言が触れていないのは 112 件中 **54 件**だった）。

    除くのは、ターゲット自身・この機構の持ち物（宣言と刻印）・隠しパス・`__pycache__` だけ。
    それ以外の「見えていないもの」は、たとえ雑音でも**事実として出す**。
    """
    base = Path(root)
    covered: set = set()
    for rule in rules:
        covered.update(expand(rule["prereqs"], root))
    skip = {r["target"] for r in rules} | {DEPS_FILE, STAMP_FILE}
    groups: dict = {}
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        parts = p.relative_to(base).parts
        if any(part.startswith(".") or part == "__pycache__" for part in parts):
            continue
        rel = "/".join(parts)
        if rel in covered or rel in skip:
            continue
        where = parts[0] if len(parts) > 1 else "(直下)"
        groups[where] = groups.get(where, 0) + 1
    ranked = sorted(groups.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"where": w, "count": n} for w, n in ranked[:limit]]


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
