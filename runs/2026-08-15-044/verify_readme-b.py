#!/usr/bin/env python3
"""verify_readme.py — README.md と実装の整合性を検査する。

2種類の件数のみを計上する:
  (1) false_statements: README.md に書かれたファイル名・役割・数が実装と食い違う件数
  (2) missing_descriptions: ファイル・役割・数について述べられていない件数

あいまいさ・詳細の記述の不足は計上しない。
結果を measure.json に {"false_statements": <int>, "missing_descriptions": <int>} 形式で出力する。
"""

import os
import re
import json
import ast

# 収集から除外するディレクトリ
EXCLUDE_DIRS = {"__pycache__", ".git", "probe_fixtures", ".mu-work", "tests"}


def collect_impl_files(base_dir):
    """実装ファイル（.py + pyproject.toml）を収集する。

    __pycache__, .git, probe_fixtures, .mu-work, tests は除外する。
    """
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        rel_root = os.path.relpath(root, base_dir).replace("\\", "/")
        parts = [p for p in rel_root.split("/") if p and p != "."]
        if any(p in EXCLUDE_DIRS for p in parts):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in filenames:
            if fname.endswith(".py") or fname == "pyproject.toml":
                rel = os.path.relpath(os.path.join(root, fname), base_dir)
                rel = rel.replace("\\", "/")
                files.append(rel)
    return sorted(files)


def get_docstring_first_line(filepath):
    """モジュールレベル docstring の先頭行を抽出する。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
        if tree.body and isinstance(tree.body[0], ast.Expr):
            val = tree.body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                ds = val.value
                if ds:
                    return ds.strip().split("\n")[0].strip()
    except Exception:
        pass
    return None


def _split_into_terms(text):
    """テキストを意味のある語に分割する。"""
    terms = set()
    # 区切り文字で分割
    parts = re.split(r"[\s/／、。，.（）()「」:：；;]+", text)
    for p in parts:
        p = p.strip()
        if len(p) >= 3:
            terms.add(p)
    # 日本語の助詞で分割
    sub_parts = re.split(r"(?:な|の|が|を|に|で|と|は|へ|から|まで|や|も|＝|＋)", text)
    for p in sub_parts:
        p = re.sub(r"[\s/／、。，.（）()「」:：；;]+", "", p).strip()
        if len(p) >= 3:
            terms.add(p)
    return terms


def extract_role_terms(docstring_first_line):
    """docstring 先頭行から役割を示すキー語を抽出する。"""
    if not docstring_first_line:
        return set()

    line = docstring_first_line

    # ファイル名前置を除去（例: "l0_chat.py — "）
    line = re.sub(r"^[\w/\-]+\.py\s*", "", line)

    # — で分割
    if "—" in line:
        parts = line.split("—", 1)
        before = parts[0].strip()
        after = parts[1].strip() if len(parts) > 1 else ""
    else:
        before = ""
        after = line

    terms = set()

    # after 部分（主たる役割記述）
    if after:
        after = re.sub(r"（合意\d+）", "", after)
        after = re.sub(r"\(合意\d+\)", "", after)
        after = after.rstrip("。. ")
        terms.update(_split_into_terms(after))

    # before 部分（記述的であれば役割情報を含む）
    if before and len(before) > 5:
        before_clean = re.sub(r"（合意\d+）", "", before)
        terms.update(_split_into_terms(before_clean))

    return terms


def check_role_in_readme(role_terms, readme_text):
    """役割が README に述べられているか判定する。"""
    if not role_terms:
        return True  # 判定不能 → 計上しない
    for term in role_terms:
        if term in readme_text:
            return True
    return False


def _looks_like_impl_file(name):
    """ファイル名が実装ファイルの命名パターンに合致するか判定する。"""
    basename = os.path.basename(name)
    if name.startswith("mu/"):
        return True
    if re.match(r"^l\d+_chat\.py$", basename):
        return True
    if basename in ("chat_common.py", "tools.py", "pyproject.toml", "__init__.py"):
        return True
    if re.match(r"^probe_\w+\.py$", basename):
        return True
    # mu/ 配下の各ファイル
    if re.match(r"^(l\d|process|role_kb|skill_kb|workspace|__init__)\.py$", basename):
        return True
    return False


def find_false_file_refs(readme_text, impl_files):
    """README に記載された存在しないファイル名を検出する。

    実装ファイルの命名パターンに合致するが実ディレクトリに存在しない
    ファイル参照を false statement として計上する。
    テストファイル・例示のファイル名は除外する。
    """
    impl_basenames = {os.path.basename(f) for f in impl_files}
    impl_paths = set(impl_files)

    # コードブロック（``` 〜 ```）を除去して例示内の参照を除外
    text_no_codeblocks = re.sub(r"```.*?```", "", readme_text, flags=re.DOTALL)

    # .py / .toml 参照を抽出
    pattern = r"`?([\w/\-]+\.py)`?|`?([\w/\-]+\.toml)`?"
    matches = re.findall(pattern, text_no_codeblocks)

    mentioned = set()
    for m in matches:
        for name in m:
            if name and len(name) > 4:
                mentioned.add(name)

    false_count = 0
    for name in mentioned:
        basename = os.path.basename(name)
        if name in impl_paths or basename in impl_basenames:
            continue
        # テストファイル・probe_fixtures は除外
        if "test_" in name or "probe_fixtures" in name:
            continue
        # 実装ファイルの命名パターンに合致するもののみ計上
        if _looks_like_impl_file(name):
            false_count += 1

    return false_count


def _check_one_number(readme_text, actual_count, explicit_patterns, vague_patterns):
    """一つの数について検査する。

    Returns: (false_count, missing_count)
      - 明示的な数が記載され実装と食い違う → (1, 0)  [false statement]
      - 明示的な数が記載され正しい         → (0, 0)  [OK]
      - 漠然とした表現がある               → (0, 0)  [あいまいさ → 計上しない]
      - 数が記載されていない               → (0, 1)  [missing description]
    """
    # 明示的な数の記述を探す
    for pattern in explicit_patterns:
        matches = re.findall(pattern, readme_text)
        for m in matches:
            stated = int(m)
            if stated != actual_count:
                return 1, 0  # false statement
            else:
                return 0, 0  # correct → no count

    # 漠然とした表現を探す（あいまいさ → 計上しない）
    for pattern in vague_patterns:
        if re.search(pattern, readme_text):
            return 0, 0  # vague → ambiguous → don't count

    # 数が記載されていない → missing
    return 0, 1


def check_number_statements(readme_text, file_count, role_count):
    """README の明示的な数の記述を検査する。

    Returns: (false_count, missing_count)
    """
    false_count = 0
    missing_count = 0

    # ファイル数の検査
    f_false, f_missing = _check_one_number(
        readme_text,
        file_count,
        explicit_patterns=[
            r"(\d+)\s*ファイル",
            r"(\d+)\s*個の.*ファイル",
            r"(\d+)\s*files",
            r"(\d+)\s*個の.*\.py",
        ],
        vague_patterns=[
            r"複数の.*ファイル",
            r"いくつかの.*ファイル",
            r"多数の.*ファイル",
            r"複数の.*\.py",
        ],
    )
    false_count += f_false
    missing_count += f_missing

    # 役割数の検査
    r_false, r_missing = _check_one_number(
        readme_text,
        role_count,
        explicit_patterns=[
            r"(\d+)\s*役割",
            r"(\d+)\s*個の.*役割",
            r"(\d+)\s*roles",
            r"(\d+)\s*個の.*docstring",
        ],
        vague_patterns=[
            r"複数の.*役割",
            r"いくつかの.*役割",
            r"多数の.*役割",
        ],
    )
    false_count += r_false
    missing_count += r_missing

    return false_count, missing_count


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 実装ファイルを収集
    impl_files = collect_impl_files(base_dir)

    # README を読み込み
    readme_path = os.path.join(base_dir, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    # 役割数（docstring を持つ .py ファイル数）をカウント
    role_count = 0
    file_docstrings = {}
    for rf in impl_files:
        if rf.endswith(".py"):
            full_path = os.path.join(base_dir, rf)
            ds = get_docstring_first_line(full_path)
            file_docstrings[rf] = ds
            if ds:
                role_count += 1

    false_statements = 0
    missing_descriptions = 0

    # --- (1) false_statements ---

    # 1a. 存在しないファイル名の参照
    false_statements += find_false_file_refs(readme_text, impl_files)

    # 1b. 数の記述の誤り
    num_false, num_missing = check_number_statements(
        readme_text, len(impl_files), role_count
    )
    false_statements += num_false

    # --- (2) missing_descriptions ---

    # 2a. ファイルが README に登場していない
    for rf in impl_files:
        basename = os.path.basename(rf)
        if basename not in readme_text and rf not in readme_text:
            missing_descriptions += 1

    # 2b. 役割が README に述べられていない
    for rf in impl_files:
        if rf.endswith(".py"):
            ds = file_docstrings.get(rf)
            if ds:
                terms = extract_role_terms(ds)
                if not check_role_in_readme(terms, readme_text):
                    missing_descriptions += 1

    # 2c. 数が記載されていない
    missing_descriptions += num_missing

    # 結果を出力
    result = {
        "false_statements": false_statements,
        "missing_descriptions": missing_descriptions,
    }

    measure_path = os.path.join(base_dir, "measure.json")
    with open(measure_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"false_statements: {false_statements}")
    print(f"missing_descriptions: {missing_descriptions}")


if __name__ == "__main__":
    main()