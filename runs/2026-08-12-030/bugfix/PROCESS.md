# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze test_stats.py and identify the requirements for the statistical functions.
   - needs: test_stats.py
   - 成功条件: The file contains a summary of the required logic from test_stats.py.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Identify and fix bugs in buggy_stats.py based on requirements in design.md.
   - needs: design.md, buggy_stats.py
   - 成功条件: The file is updated to fix calculation errors, boundary conditions, and type conversions.
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that buggy_stats.py passes all tests defined in test_stats.py.
   - needs: design.md, buggy_stats.py, test_stats.py
   - 成功条件: The output of python test_stats.py includes 'OK'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python test_stats.py` → 「OK」
