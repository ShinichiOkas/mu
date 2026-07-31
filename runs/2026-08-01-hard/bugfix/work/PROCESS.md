# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze buggy_stats.py and test_stats.py to identify bugs and design the necessary fixes to make all tests pass without modifying the test file.
   - 成功条件: The design document identifies all failures in the current implementation and specifies the corrections needed.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Implement the fixes in buggy_stats.py based on the design document.
   - 成功条件: The bugs are fixed and the code is syntactically correct.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that buggy_stats.py passes all tests and ensure that test_stats.py has not been modified.
   - 成功条件: The tests report 'OK' and the SHA-256 hash of test_stats.py remains unchanged.
   - 検査: `python test_stats.py` → 「OK」
