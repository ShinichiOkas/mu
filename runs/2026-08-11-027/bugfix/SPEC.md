# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: PowerShellで 'python test_stats.py' を実行し、標準出力に 'OK' という文字列が含まれている状態

## 受入基準
1. [ ] buggy_stats.py が修正されており、test_stats.py の実行結果に 'OK' が表示されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
2. [ ] test_stats.py のファイル内容が変更されていないこと（検査: `Get-Content test_stats.py`）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` の全テストをパスさせる。

【制約】
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正対象は `buggy_stats.py` のみとする。

【完了定義】
以下の検証基準をすべて満たしたとき、本タスクは完了とする。

1. 動作検証: 
   PowerShellで `python test_stats.py` を実行し、出力に `OK` という文字列が含まれていること。
2. 不変性の検証:
   `test_stats.py` の内容が元の状態から変更されていないこと。

【成果物】
- 修正済み `buggy_stats.py`
