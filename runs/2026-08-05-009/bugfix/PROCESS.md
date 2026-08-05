# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze buggy_stats.py and test_stats.py to identify the bugs. Define the fix plan for mean, median, variance, and value_range to ensure all tests pass without modifying the test file.
   - 成功条件: The design document must list all identified bugs and the corresponding corrective logic for each function.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in buggy_stats.py based on design.md. Ensure that the logic handles edge cases and precision as required by test_stats.py.
   - 成功条件: The code must be syntactically correct and aim to pass all tests in test_stats.py.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that all tests in test_stats.py pass and confirm that test_stats.py has not been modified.
   - 成功条件: Both the test execution result (OK) and the integrity of test_stats.py must be confirmed. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `python test_stats.py` → 「OK」
