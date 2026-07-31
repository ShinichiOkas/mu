# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
jsonparse.py 1ファイルで、標準ライブラリの json モジュールを一切使わずに JSON パーサを実装してくれ。parse(text) が dict/list/str/int/float/bool/None を返す。ネスト・文字列エスケープ（\" \\ \n \uXXXX）・数値（負数・小数・指数）・空配列/空オブジェクト・null/true/false を網羅する20件以上のセルフテストが python jsonparse.py --selftest で走り、全部通れば 'JSONPARSE OK <件数>' を表示して exit 0。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design a recursive descent JSON parser that supports standard JSON types, escape sequences (including \uXXXX), and scientific notation without using the 'json' module. Specify the internal tokenization and parsing strategy in the design document.
   - 成功条件: Design covers: tokenization, recursive descent parsing for objects/arrays/strings/numbers, and the mapping of JSON types to Python types.
2. [ ] **implementer** → `jsonparse.py`
   - task: Implement the JSON parser in `jsonparse.py` as specified in the design. Ensure the `parse(text)` function is provided. Implement the CLI entry point that runs a self-test suite of at least 20 cases (covering nested structures, empty objects/arrays, escaped characters, negative numbers, floats, scientific notation, booleans, and null) and prints 'JSONPARSE OK <count>' upon success.
   - 成功条件: The file must not contain 'import json' or 'from json import'. It must handle all specified numeric and string formats.
   - 検査: `python jsonparse.py --selftest` → 「JSONPARSE OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that `jsonparse.py` meets all specification requirements: existence, prohibition of the json module, correct parsing of all JSON types/formats, and success of the 20+ self-tests.
   - 成功条件: Independent verification of all criteria listed in the SPEC.
   - 検査: `Get-Content jsonparse.py | Select-String 'import json', 'from json import'`
