# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: PowerShell で `python test_stats.py` を実行し、標準出力に文字列 『OK』 が含まれている状態でプロセスが正常終了すること

## 受入基準
1. [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py`）
2. [ ] buggy_stats.py の修正後、test_stats.py を実行して OK が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` による検証をすべてパスさせる。

【制約】
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正は `buggy_stats.py` の内部実装のみで行う。

【完了定義】
以下の基準をすべて満たしたとき、本タスクは完了とする。
1. `test_stats.py` のファイル内容が、修正前と同一であること。
2. 実行環境（Windows 11 / PowerShell）において、コマンド `python test_stats.py` を実行した際、標準出力に 『OK』 という文字列が表示され、エラーなく終了すること。

【成果物】
- 修正済みの `buggy_stats.py`
