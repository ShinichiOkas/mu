# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: Windows PowerShell 上で `python test_stats.py` を実行し、標準出力に文字列 'OK' が含まれ、かつ終了コードが 0 であること

## 受入基準
1. [ ] test_stats.py が変更されていないこと（検査: `Get-FileHash test_stats.py`）
2. [ ] python test_stats.py の実行結果に 'OK' が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` で定義された仕様をすべて満たすこと。

【制約】
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正は `buggy_stats.py` 内で完結させること。

【定義】
- すべてのテストが通る：Windows PowerShell 上で `python test_stats.py` を実行した際、標準出力に 'OK' と表示され、プロセスが正常終了すること。

【完了基準】
1. `test_stats.py` のファイル内容が、作業前と同一であること（Get-FileHash 等で確認）。
2. `python test_stats.py` を実行し、出力に 'OK' という文字列が含まれていること。

【納品物】
- 修正済み `buggy_stats.py`
