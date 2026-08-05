# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the bugs in `buggy_stats.py` by comparing its implementation with the requirements implied by `test_stats.py`. Document the necessary fixes for `mean`, `median`, `variance`, and `value_range`, including edge case handling for empty lists.
   - 成功条件: The design document must list all identified bugs and the corrected logic for each function.
2. [ ] **implementer** → `buggy_stats.py`
   - task: Fix the bugs in `buggy_stats.py` based on the design document. Ensure that all statistical functions handle empty lists and edge cases correctly as specified.
   - 成功条件: The code must be syntactically correct and attempt to resolve all bugs identified in design.md.
   - 検査: `python test_stats.py` → 「OK」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that `buggy_stats.py` passes all tests in `test_stats.py` and confirm that `test_stats.py` has not been modified.
   - 成功条件: Both the test execution output must contain 'OK' and the integrity check of test_stats.py must pass.
   - 検査: `python test_stats.py; Get-Content test_stats.py` → 「OK」
