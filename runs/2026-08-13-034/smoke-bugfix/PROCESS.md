# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the bugs in `buggy_stats.py` by examining the test failures from `python test_stats.py`. Create a plan to fix the logic in `buggy_stats.py` to satisfy all tests without modifying `test_stats.py`.
   - needs: buggy_stats.py, test_stats.py
   - 成功条件: The design document identifies the causes of failures and describes the necessary fixes for `buggy_stats.py`.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in `buggy_stats.py` based on the design document. Ensure that the implementation handles all edge cases tested by `test_stats.py`.
   - needs: design.md, buggy_stats.py
   - 成功条件: The code is syntactically correct and modified to fix the identified bugs.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that `buggy_stats.py` passes all tests and that `test_stats.py` remains unchanged. Confirm that the output of `python test_stats.py` contains 'OK' and the exit code is 0.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: The verdict confirms that both acceptance criteria (no change to test_stats.py and successful execution) are met. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
