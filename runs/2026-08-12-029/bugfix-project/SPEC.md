# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **テストが通る**: PowerShellで `python test_stats.py` を実行し、標準出力に文字列 "OK" が含まれ、かつ終了コードが 0 であること。

## 受入基準
1. [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py`）
2. [ ] buggy_stats.py の修正後、テスト実行結果に 'OK' が表示されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` ですべてのテストケースをパスさせる。

【制約】
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正は `buggy_stats.py` の内部のみで行う。

【定義】
- テストが通る：PowerShellで `python test_stats.py` を実行し、標準出力に文字列 "OK" が含まれ、かつ終了コードが 0 であること。

【納品物】
- 修正済みの `buggy_stats.py`

【完了基準（検査項目）】
1. `test_stats.py` のファイル内容が変更されていないこと。
2. `python test_stats.py` を実行した際、出力に "OK" という文字列が含まれていること。
