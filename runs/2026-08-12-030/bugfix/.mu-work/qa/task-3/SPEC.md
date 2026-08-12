# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **all tests pass**: The execution of 'python test_stats.py' results in an exit code of 0 and the string 'OK' appears in the standard output for every test case defined within it.

## 受入基準
1. [ ] The script buggy_stats.py is modified to resolve all logic errors.
2. [ ] Running the test suite results in a success message.（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
【目的】
test_stats.py で定義されている仕様を完全に満たすように buggy_stats.py を修正する。この際、test_stats.py は一切変更してはならない。

【定義】
- すべてのテストが通る： python test_stats.py を実行した際に、終了コード 0 が返され、標準出力に 'OK' という文字列が含まれること。

【詳細仕様】
1. `test_stats.py` を読み取り、定義されている統計機能の要件を特定せよ。
2. `buggy_stats.py` 内のバグ（計算ミス、境界条件の誤り、型変換の失敗など）を特定し、修正せよ。
3. 修正後の `buggy_stats.py` を使用して `python test_stats.py` を実行し、すべてのテストが成功することを確認せよ。

【成果物】
- 修理済みの `buggy_stats.py` ファイル。
