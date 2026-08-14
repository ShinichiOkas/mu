"""verify_readme.py — README.md と実装ファイル群を照合し、false_claims と
missing_mentions を数えて標準出力と measure.json に出力する。

Python 標準ライブラリのみ使用。README.md および実装ファイルは読み取り専用。
書き込むのは measure.json のみ。
"""

import os
import re
import json


# ──────────────────────────────────────────────
# 1. 対象ファイル発見
# ──────────────────────────────────────────────

def discover_files():
    """ディスクを走査して実装ファイル群を動的に発見する。

    戻り値: (mu_py_files, root_py_files, has_pyproject, docs_md_files)
      - mu_py_files: mu/ 配下の .py ファイル名のリスト（拡張子付き）
      - root_py_files: ルートの .py ファイル名のリスト（拡張子付き）
      - has_pyproject: pyproject.toml が存在するか bool
      - docs_md_files: docs/ 配下の .md ファイル名のリスト
    """
    mu_py = []
    if os.path.isdir("mu"):
        for name in sorted(os.listdir("mu")):
            if name.endswith(".py"):
                mu_py.append(name)

    root_py = []
    for name in sorted(os.listdir(".")):
        if name.endswith(".py"):
            root_py.append(name)

    has_pyproject = os.path.isfile("pyproject.toml")

    docs_md = []
    if os.path.isdir("docs"):
        for name in sorted(os.listdir("docs")):
            if name.endswith(".md"):
                docs_md.append(name)

    return mu_py, root_py, has_pyproject, docs_md


# ──────────────────────────────────────────────
# 2. 役割（role）の発見
# ──────────────────────────────────────────────

# コードが名前で知る4ポジション（合意024）。
# roles/ になくても実装に存在する役割として扱う。
CORE_POSITIONS = {"pdm", "pjm", "architect", "implementer", "qa"}

def discover_roles():
    """roles/ ディレクトリから役割名を抽出する。

    roles/<package>/*.md のファイル名（拡張子除く）を役割名とする。
    roles/ 直下の .md ファイル（director.md, learner.md 等）も役割名に含める。
    roles/ が存在しない場合はコアポジションのみ返す。

    戻り値: 役割名の set
    """
    roles = set()
    if os.path.isdir("roles"):
        # roles/ 直下の .md ファイル
        for name in sorted(os.listdir("roles")):
            full = os.path.join("roles", name)
            if os.path.isfile(full) and name.endswith(".md"):
                roles.add(name[:-3])  # 拡張子除く
            elif os.path.isdir(full):
                # サブディレクトリ内の .md ファイル
                for sub in sorted(os.listdir(full)):
                    if sub.endswith(".md"):
                        roles.add(sub[:-3])
    # コアポジションは必ず含む（roles/ になくても実装に存在する役割）
    roles |= set(CORE_POSITIONS)
    return roles


# ──────────────────────────────────────────────
# 3. 層（L0〜L5）と役割の対応関係
# ──────────────────────────────────────────────

def discover_layers():
    """mu/ 配下の l0.py〜l5.py の存在から層を特定する。

    戻り値: 層名のリスト（["L0", "L1", ...]）
    """
    layers = []
    if os.path.isdir("mu"):
        for i in range(6):
            if os.path.isfile(f"mu/l{i}.py"):
                layers.append(f"L{i}")
    return layers


def discover_layer_role_mapping():
    """実装ファイルから層と役割の対応関係を抽出する。

    mu/l4.py の docstring から "PjM"、mu/l5.py から "PdM" を特定する。
    l0〜l3 は役割を持たない（汎用層）。

    戻り値: {層名: 役職名（小文字）} の dict
    """
    mapping = {}
    # l4.py の docstring から PjM を特定
    try:
        with open("mu/l4.py", encoding="utf-8") as f:
            head = f.read(500)
        if "PjM" in head or "pjm" in head.lower():
            mapping["L4"] = "pjm"
    except (OSError, UnicodeDecodeError):
        pass

    # l5.py の docstring から PdM を特定
    try:
        with open("mu/l5.py", encoding="utf-8") as f:
            head = f.read(500)
        if "PdM" in head or "pdm" in head.lower():
            mapping["L5"] = "pdm"
    except (OSError, UnicodeDecodeError):
        pass

    return mapping


# ──────────────────────────────────────────────
# 4. README.md の読み込みと前処理
# ──────────────────────────────────────────────

def load_readme_lines():
    """README.md を読み込み、コードブロック外の行のリストを返す。

    ``` で囲まれたコードブロック内の行は除外する。
    """
    try:
        with open("README.md", encoding="utf-8") as f:
            raw_lines = f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    result = []
    in_code_block = False
    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            result.append(line)
    return result


def load_readme_full_text():
    """README.md の全文（コードブロック含む）を返す。
    missing_mentions の言及確認に使う。
    """
    try:
        with open("README.md", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


# ──────────────────────────────────────────────
# 5. false_claims 計測
# ──────────────────────────────────────────────

def is_format_only_line(line):
    """markdown の書式要素のみの行（見出し記号、区切り線、テーブルヘッダー等）
    かどうかを判定する。ただし見出し行にファイル名や役割名が含まれていれば
    内容があるため False を返す。
    """
    stripped = line.strip()
    if not stripped:
        return True
    # 区切り線のみ
    if re.match(r'^[-*_]+$', stripped):
        return True
    # テーブルの区切り行 (|---|---| 等)
    if re.match(r'^[\s|:-]+$', stripped) and '|' in stripped:
        return True
    return False


def check_false_claims_line(line, all_impl_files, actual_file_count,
                            roles_set, actual_role_count, layer_role_map):
    """README.md の1行を照合し、false_claims に該当するか判定する。

    1行につき最大1件。パターン (A)〜(E) を順に試す。
    該当する場合は True、しない場合は False を返す。
    """
    if is_format_only_line(line):
        return False

    # (A) 存在しないファイル名の記載
    # .py 拡張子付きのファイル名を検出
    py_refs = re.findall(r'(?:mu/)?([A-Za-z_][A-Za-z0-9_]*\.py)', line)
    for ref in py_refs:
        # mu/XXX.py の形で書かれている場合
        mu_match = re.search(r'mu/([A-Za-z_][A-Za-z0-9_]*\.py)', line)
        # 検出したファイル名が実装ファイル群に存在するか確認
        bare_name = ref
        # all_impl_files には mu/ 配下は "mu/xxx.py" 形式、ルートは "xxx.py" 形式が入っている想定
        found = False
        for impl in all_impl_files:
            if impl.endswith("/" + bare_name) or impl == bare_name:
                found = True
                break
        if not found:
            return True

    # (B) ファイル数の矛盾
    # 「Nファイル」「N files」「N file」「N個のファイル」等の数値表現
    file_count_patterns = [
        r'(\d+)\s*(?:ファイル|files|file)',
        r'(\d+)\s*(?:個の)?ファイル',
    ]
    for pat in file_count_patterns:
        m = re.search(pat, line, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if n != actual_file_count:
                return True

    # (C) 実装にない役割の記載
    # README.md に役割名が記載されており、それが roles_set に存在しない場合。
    # ただし「将来追加する」「これから」等の文脈は除外。
    # 役割名らしき英単語を検出（小文字で roles_set と比較）
    future_keywords = ['これから', '将来', '予定', '未実装', '計画', 'future', 'plan']
    is_future_context = any(kw in line.lower() for kw in future_keywords)
    if not is_future_context:
        # バッククォートまたは通常テキスト内の役割名を検出
        # 英小文字の単語を抽出
        words_in_line = set(re.findall(r'\b([a-z]+)\b', line.lower()))
        for word in words_in_line:
            # roles_set にない役割名で、かつ英単語として意味のあるもの
            # ただし一般的な英単語は役割名ではないので、既知の役割名パターンに限定
            # roles_set の中から、行に含まれるものを確認するのは逆方向
            # ここでは: 行に「実装済み」「実証済み」等の文脈で未知の役割名があるか
            pass
        # より具体的なアプローチ: roles_set にない名前が役割として明示されているか
        # 役割名のパターン（role: xxx, 役割 xxx, xxx役割 等）を検出
        role_mentions = re.findall(r'(?:role|役割)[:：]\s*(\w+)', line, re.IGNORECASE)
        for rm in role_mentions:
            if rm.lower() not in roles_set:
                return True

    # (D) 役割数の矛盾
    role_count_patterns = [
        r'(\d+)\s*(?:役割|roles|role)',
        r'(\d+)\s*(?:個の)?役割',
    ]
    for pat in role_count_patterns:
        m = re.search(pat, line, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if n != actual_role_count:
                return True

    # (E) 層と役割の対応関係の矛盾
    # 「LX = 役割Y」または「LX（役割Y）」「LX: 役割Y」等の明示的な対応
    # README.md に書かれている対応を抽出
    layer_role_patterns = [
        r'L(\d)\s*[=＝:：]\s*([A-Za-z]+)',
        r'L(\d)\s*[（(]\s*([A-Za-z]+)\s*[)）]',
        r'L(\d)\s*[（(]\s*(\w+)\s*[)）]',
    ]
    for pat in layer_role_patterns:
        m = re.search(pat, line)
        if m:
            layer_num = m.group(1)
            role_name = m.group(2).lower()
            layer_key = f"L{layer_num}"
            if layer_key in layer_role_map:
                if role_name != layer_role_map[layer_key]:
                    return True

    return False


def count_false_claims(readme_lines, all_impl_files, actual_file_count,
                       roles_set, actual_role_count, layer_role_map):
    """false_claims を計測する。行単位でカウント（1行最大1件）。"""
    count = 0
    for line in readme_lines:
        if check_false_claims_line(line, all_impl_files, actual_file_count,
                                   roles_set, actual_role_count, layer_role_map):
            count += 1
    return count


# ──────────────────────────────────────────────
# 6. missing_mentions 計測
# ──────────────────────────────────────────────

def count_missing_mentions(readme_full_text, mu_py_files, root_py_files,
                           has_pyproject, docs_md_files, roles_set, layers,
                           actual_file_count, actual_role_count):
    """missing_mentions を計測する。要素単位でカウント。"""
    count = 0
    readme_lower = readme_full_text.lower()

    # 6.1 ファイルの言及確認
    # mu/ 配下の .py ファイル
    for name in mu_py_files:
        mu_path = f"mu/{name}"
        if mu_path in readme_full_text or name in readme_full_text:
            continue
        # __init__.py は特別扱い: mu/__init__.py または __init__ の言及があればよい
        if name == "__init__.py":
            if "mu/__init__.py" in readme_full_text or "__init__" in readme_full_text:
                continue
        # 層ファイル (l0.py〜l5.py) は層名 L0〜L5 が言及されていればよい
        layer_match = re.match(r'l(\d)\.py', name)
        if layer_match:
            layer_name = f"L{layer_match.group(1)}"
            if layer_name in readme_full_text:
                continue
        count += 1

    # ルートの .py ファイル
    for name in root_py_files:
        if name in readme_full_text:
            continue
        # 層チャットファイル (l0_chat.py〜l5_chat.py) は対応する記述があればよい
        chat_match = re.match(r'l(\d)_chat\.py', name)
        if chat_match:
            # l{N}_chat または L{N} の言及があればよい
            if f"l{chat_match.group(1)}_chat" in readme_full_text.lower() or \
               f"L{chat_match.group(1)}" in readme_full_text:
                continue
        count += 1

    # pyproject.toml
    if has_pyproject:
        if "pyproject.toml" not in readme_full_text and "pyproject" not in readme_full_text:
            count += 1

    # docs/ 配下の .md ファイル
    for name in docs_md_files:
        docs_path = f"docs/{name}"
        if docs_path in readme_full_text or name in readme_full_text:
            continue
        count += 1

    # 6.2 役割の言及確認
    for role in sorted(roles_set):
        if role.lower() in readme_lower:
            continue
        count += 1

    # 層名（L0, L1, ..., L5）の言及確認
    for layer in layers:
        if layer in readme_full_text:
            continue
        # 層に対応するファイル名 (l0.py 等) が言及されていればよい
        layer_num = layer[1:]  # "L0" -> "0"
        if f"l{layer_num}.py" in readme_full_text.lower():
            continue
        count += 1

    # 6.3 ファイル数・役割数の言及確認
    # ファイル数についての言及（数値表現、または「すべてのファイル」「全ファイル」等）
    has_file_count_mention = bool(
        re.search(r'\d+\s*(?:ファイル|files?|file)', readme_full_text, re.IGNORECASE)
        or 'すべてのファイル' in readme_full_text
        or '全ファイル' in readme_full_text
        or 'すべての.py' in readme_full_text
        or '全ファイル' in readme_full_text
    )
    if not has_file_count_mention:
        count += 1

    # 役割数についての言及（数値表現、または「すべての役割」「全役割」等）
    has_role_count_mention = bool(
        re.search(r'\d+\s*(?:役割|roles?|role)', readme_full_text, re.IGNORECASE)
        or 'すべての役割' in readme_full_text
        or '全役割' in readme_full_text
        or 'すべてのrole' in readme_lower
        or '全role' in readme_lower
    )
    if not has_role_count_mention:
        count += 1

    return count


# ──────────────────────────────────────────────
# 7. メイン処理
# ──────────────────────────────────────────────

def main():
    # 1. 対象ファイル発見
    mu_py_files, root_py_files, has_pyproject, docs_md_files = discover_files()

    # 実装ファイルのフルパスリスト（存在確認用）
    all_impl_files = []
    for name in mu_py_files:
        all_impl_files.append(f"mu/{name}")
    for name in root_py_files:
        all_impl_files.append(name)

    # 2. 役割発見
    roles_set = discover_roles()

    # 3. 層発見
    layers = discover_layers()

    # 層と役割の対応関係
    layer_role_map = discover_layer_role_mapping()

    # 4. ファイル数・役割数の算出
    # ファイル数: mu/ 配下の .py + ルートの .py + pyproject.toml (1) の合計
    actual_file_count = len(mu_py_files) + len(root_py_files) + (1 if has_pyproject else 0)

    # 役割数: roles/ ディレクトリ内の役割名の数（重複排除）
    # コアポジションは必ず含むが、roles/ から発見された役割の数を数える
    # design.md 2.3: 役割数 = roles/ ディレクトリ内の .md ファイル数
    # ただし重複する役割名（複数パッケージにまたがるもの）は1つとして数える
    actual_role_count = len(discover_roles())

    # 5. README.md 読み込み
    readme_lines = load_readme_lines()
    readme_full_text = load_readme_full_text()

    # 6. false_claims 計測
    false_claims = count_false_claims(
        readme_lines, all_impl_files, actual_file_count,
        roles_set, actual_role_count, layer_role_map
    )

    # 7. missing_mentions 計測
    missing_mentions = count_missing_mentions(
        readme_full_text, mu_py_files, root_py_files,
        has_pyproject, docs_md_files, roles_set, layers,
        actual_file_count, actual_role_count
    )

    # 8. 結果出力
    print(f"false_claims: {false_claims}, missing_mentions: {missing_mentions}")

    result = {"false_claims": false_claims, "missing_mentions": missing_mentions}
    with open("measure.json", "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()