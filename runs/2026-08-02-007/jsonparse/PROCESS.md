# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
jsonparse.py 1ファイルで、標準ライブラリの json モジュールを一切使わずに JSON パーサを実装してくれ。parse(text) が dict/list/str/int/float/bool/None を返す。ネスト・文字列エスケープ（\" \\ \n \uXXXX）・数値（負数・小数・指数）・空配列/空オブジェクト・null/true/false を網羅する20件以上のセルフテストが python jsonparse.py --selftest で走り、全部通れば 'JSONPARSE OK <件数>' を表示して exit 0。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design a recursive descent parser for JSON that avoids the 'json' module. Define the grammar for tokens (strings, numbers, booleans, null, objects, arrays) and a strategy for handling escape sequences (especially \uXXXX) and scientific notation. Plan the 20+ self-test cases covering all boundary conditions specified in the SPEC.
   - 成功条件: The design must explicitly describe how to implement the parser without the json module and list at least 20 test cases.
2. [ ] **implementer** → `jsonparse.py`
   - task: Implement the JSON parser in jsonparse.py based on design.md. Ensure no 'import json' is present. Implement the parse(text) function and the --selftest CLI logic that outputs 'JSONPARSE OK <count>' upon success.
   - 成功条件: The file must contain the parse function, handle all required escape sequences and number formats, and pass the internal self-tests.
   - 検査: `python jsonparse.py --selftest` → 「JSONPARSE OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that jsonparse.py does not import the json module and passes the self-test suite. Independently check the implementation against the SPEC requirements (Unicode escapes, scientific notation, etc.).
   - 成功条件: The verdict must confirm: 1) Absence of 'import json'. 2) Successful execution of 20+ tests. 3) Correct handling of specified JSON types and escapes.
   - 検査: `Get-Content jsonparse.py`
