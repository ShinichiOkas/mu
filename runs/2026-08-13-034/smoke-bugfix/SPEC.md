# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: Windows PowerShell 上で `python test_stats.py` を実行した際、標準出力に文字列 'OK' が含まれ、かつ終了コードが 0 であること

## 受入基準
1. [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py`）
2. [ ] python test_stats.py の実行結果に 'OK' が含まれていること（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` で定義されたすべてのテストをパスさせる。

【制約】
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正は `buggy_stats.py` のみに行う。

【完了定義】
以下の基準をすべて満たした状態で `buggy_stats.py` を提出すること：
1. `test_stats.py` の内容が、作業前から一切変更されていないこと。
2. Windows PowerShell 環境で `python test_stats.py` を実行した際、標準出力に『OK』と表示され、正常終了すること。

【納品物】
- 修正済みの `buggy_stats.py`
