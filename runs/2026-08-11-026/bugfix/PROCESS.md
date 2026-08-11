# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## タスク列
1. [ ] **implementer** → `buggy_stats.py`
   - task: Analyze the bugs in buggy_stats.py by examining its code and the failures reported by test_stats.py, then fix the bugs to ensure all tests pass.
   - 成功条件: The script buggy_stats.py is corrected such that running test_stats.py results in 'OK'.
   - 検査: `python test_stats.py` → 「OK」
2. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that buggy_stats.py is fixed and that the read-only file test_stats.py has not been modified.
   - 成功条件: Both criteria in the SPEC are met: test_stats.py is unchanged and python test_stats.py outputs 'OK'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python test_stats.py` → 「OK」
