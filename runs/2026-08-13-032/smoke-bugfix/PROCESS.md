# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the current behavior of buggy_stats.py and the requirements defined in test_stats.py. Identify the bugs and design the fixes needed to make the tests pass.
   - needs: buggy_stats.py, test_stats.py
   - 成功条件: The design document must identify the cause of the failure and describe the specific logic changes required in buggy_stats.py.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in buggy_stats.py based on the design document to ensure that python test_stats.py returns 'OK'.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: The file buggy_stats.py is updated, and running 'python test_stats.py' in PowerShell results in 'OK' being printed.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the bugfix is successful and that the test script itself has not been modified.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: Both criteria (test_stats.py unchanged and python test_stats.py outputting 'OK') must be explicitly confirmed. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python test_stats.py` → 「OK」
