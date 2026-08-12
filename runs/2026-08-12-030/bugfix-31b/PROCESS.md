# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Analyze the current state of buggy_stats.py and test_stats.py to identify the bugs. Define the required fixes to ensure test_stats.py passes.
   - needs: buggy_stats.py, test_stats.py
   - 成功条件: The design document must clearly list the bugs found and the plan to fix them in buggy_stats.py.
2. [x] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in buggy_stats.py according to the design document. Ensure no changes are made to test_stats.py.
   - needs: design.md, buggy_stats.py
   - 成功条件: The script should be syntactically correct and aimed at passing the tests.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that buggy_stats.py passes all tests and that test_stats.py has not been modified.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: Confirm that python test_stats.py outputs 'OK' and that the original test file is untouched. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
