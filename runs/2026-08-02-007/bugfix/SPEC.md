# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: Windows PowerShell で `python test_stats.py` を実行した際、標準出力に 'OK' という文字列が含まれている状態

## 受入基準
- [ ] test_stats.py を実行して 'OK' が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
- [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py` → 出力に「stats の仕様を定めるテスト。このファイルは変更禁止（読み取り専用）。」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` の全テストケースをパスさせる。

【制約】
1. `test_stats.py` は一切変更してはならない（読み取り専用）。
2. 修正は `buggy_stats.py` のみに行う。

【定義】
- 「すべてのテストが通る」状態：`python test_stats.py` を実行し、出力に 'OK' が含まれること。

【成果物】
- 修正済み `buggy_stats.py`

【検証方法】
- 実行コマンド: `python test_stats.py`
- 期待される出力: `OK`
