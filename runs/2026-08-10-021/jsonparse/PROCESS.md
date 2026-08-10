# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
jsonparse.py 1ファイルで、標準ライブラリの json モジュールを一切使わずに JSON パーサを実装してくれ。parse(text) が dict/list/str/int/float/bool/None を返す。ネスト・文字列エスケープ（\" \\ \n \uXXXX）・数値（負数・小数・指数）・空配列/空オブジェクト・null/true/false を網羅する20件以上のセルフテストが python jsonparse.py --selftest で走り、全部通れば 'JSONPARSE OK <件数>' を表示して exit 0。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the JSON parser architecture. Define the recursive descent parsing strategy for objects, arrays, strings (including escape sequence handling), and numbers (including scientific notation). Plan the structure of the --selftest suite with 20+ cases to cover all requirements.
   - 成功条件: The design document must explicitly detail how to handle \uXXXX, scientific notation, and the recursive structure without using the json module.
2. [ ] **implementer** → `jsonparse.py`
   - task: Implement the JSON parser in jsonparse.py. Create the parse(text) function and the --selftest CLI logic. Ensure 'import json' is not used. Implement support for dict, list, str, int, float, bool, and None. Include 20+ test cases as specified in the design.
   - 成功条件: The file must be runnable and pass the self-test command provided in the spec.
   - 検査: `python jsonparse.py --selftest` → 「JSONPARSE OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Independently verify the implementation against the SPEC. Check for the presence of 'import json', verify the correctness of escape sequence handling, number parsing, and the execution of the self-test suite. Verify that it returns the correct Python types.
   - 成功条件: The verdict must confirm that all criteria in the SPEC are met, especially the prohibition of the json module and the output of the self-test. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
