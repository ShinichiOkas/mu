# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **all tests pass**: The execution of the command `python test_stats.py` results in a standard output containing the string 'OK'.
- **without changing test_stats.py**: The SHA-256 hash of `test_stats.py` before and after the modification of `buggy_stats.py` must be identical.

## 受入基準
- [ ] The test suite reports OK（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
Fix all bugs in `buggy_stats.py` such that the existing test suite in `test_stats.py` passes completely. 

Definitions:
- All tests pass: The execution of `python test_stats.py` results in a standard output containing the string 'OK'.
- Without changing test_stats.py: The file `test_stats.py` must remain unmodified.

Deliverable:
- A corrected version of `buggy_stats.py`.

Verification:
- Run `python test_stats.py` and verify that the output contains 'OK'.
