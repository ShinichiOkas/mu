# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
jsonparse.py 1ファイルで、標準ライブラリの json モジュールを一切使わずに JSON パーサを実装してくれ。parse(text) が dict/list/str/int/float/bool/None を返す。ネスト・文字列エスケープ（\" \\ \n \uXXXX）・数値（負数・小数・指数）・空配列/空オブジェクト・null/true/false を網羅する20件以上のセルフテストが python jsonparse.py --selftest で走り、全部通れば 'JSONPARSE OK <件数>' を表示して exit 0。

## 操作的定義
- **json module prohibition**: The source code of jsonparse.py must not contain the string 'import json' or 'from json import'.
- **standard JSON types**: The parse(text) function must return Python types: dict (for {}), list (for []), str (for ""), int/float (for numbers), bool (for true/false), and None (for null).
- **string escape sequences**: The parser must correctly transform the following sequences in JSON strings to Python characters: \" to ", \\ to \, \n to newline, and \uXXXX to the corresponding Unicode character.
- **numeric formats**: The parser must handle negative signs (-), decimals (.), and scientific notation (e/E).
- **selftest suite**: A set of at least 20 test cases containing: nested structures, empty objects/arrays, escaped characters, negative numbers, floats, scientific notation, and all boolean/null values.

## 受入基準
- [ ] The file jsonparse.py exists.（検査: `Get-ChildItem jsonparse.py` → 出力に「jsonparse.py」を含むこと）
- [ ] The code does not use the json module.（検査: `Get-Content jsonparse.py | Select-String 'import json', 'from json import'`）
- [ ] The self-test suite runs and passes at least 20 tests, printing the required success marker.（検査: `python jsonparse.py --selftest` → 出力に「JSONPARSE OK」を含むこと）

## 仕様
Implement a JSON parser in a single file named `jsonparse.py` without using the standard `json` library.

Definitions:
- json module prohibition: The source code must not contain 'import json' or 'from json import'.
- standard JSON types: parse(text) returns Python dict, list, str, int, float, bool, or None.
- string escape sequences: Support \", \\, \n, and \uXXXX.
- numeric formats: Support negative numbers, decimals, and scientific notation (e.g., -1.23e10).
- selftest suite: A minimum of 20 test cases covering nesting, empty structures, escapes, and all primitive types.

Deliverable:
- `jsonparse.py`: Contains a `parse(text)` function and a CLI entry point that executes self-tests when `--selftest` is passed.

Verification:
- Running `python jsonparse.py --selftest` must output the string 'JSONPARSE OK <count>' where <count> is >= 20, and exit with code 0.
