# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze buggy_stats.py and test_stats.py to identify the bugs causing test failures. Design a fix that satisfies all test cases without modifying the test file.
   - 成功条件: The design document must list the identified bugs and the planned corrections for buggy_stats.py.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in buggy_stats.py based on the design.md. Ensure the implementation is robust and passes all criteria in test_stats.py.
   - 成功条件: The code should be logically correct and not contain syntax errors.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that buggy_stats.py passes all tests and that test_stats.py remains unchanged as per the spec.
   - 成功条件: Both the test execution output 'OK' and the integrity of test_stats.py must be confirmed.
   - 検査: `python test_stats.py; Get-Content test_stats.py` → 「OK」
