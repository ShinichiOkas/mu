# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the bugs in `buggy_stats.py` by running `python test_stats.py` and reviewing the code. Design the fix required to satisfy the tests without modifying `test_stats.py`.
   - 成功条件: The design document must identify the cause of the failure and describe the specific logic changes needed in `buggy_stats.py`.
   - 検査: `Get-Content design.md` → 「cause」
2. [ ] **implementer** → `buggy_stats.py`
   - task: Apply the fixes to `buggy_stats.py` based on the design document. Ensure no changes are made to `test_stats.py`.
   - 成功条件: The script `test_stats.py` must output 'OK' and exit with code 0 when run.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that `test_stats.py` remains unchanged and that `python test_stats.py` returns 'OK'.
   - 成功条件: Both the immutability of the test file and the successful execution of tests are confirmed. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python test_stats.py` → 「OK」
