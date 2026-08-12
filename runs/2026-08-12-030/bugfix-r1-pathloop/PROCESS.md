# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze test_stats.py to understand the required logic and requirements.
   - needs: test_stats.py
   - 成功条件: A summary of the requirements derived from test_stats.py is documented in design.md.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix logic in buggy_stats.py based on the analysis and design document.
   - needs: design.md, buggy_stats.py
   - 成功条件: The file is updated to fix internal logic while maintaining existing interfaces.
3. [ ] **qa** → `verdict.md`
   - task: Verify that test_stats.py passes and remains unchanged.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: The validation of the run command 'python test_stats.py' finds 'OK' and the file count for test_stats.py is consistent. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python test_stats.py` → 「OK」
