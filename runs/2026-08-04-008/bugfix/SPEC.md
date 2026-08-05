# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: PowerShellで `python test_stats.py` を実行し、標準出力に 'OK' という文字列が含まれている状態。

## 受入基準
- [ ] test_stats.py のすべてのテストケースに合格し、OK が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
- [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py` → 出力に「"""stats の仕様を定めるテスト。このファイルは変更禁止（読み取り専用）。"""」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` で定義されたすべての統計計算テストをパスさせる。

【制約】
1. `test_stats.py` は読み取り専用とし、一切の変更を禁止する。
2. `buggy_stats.py` の修正のみで対応すること。

【修正対象】
- `buggy_stats.py` 内の `mean`, `median`, `variance`, `value_range` 等の関数における計算ロジック、エッジケース（空リスト等）の処理。

【完了基準】
- 以下のコマンドを実行し、出力に 'OK' が含まれていること。
  `python test_stats.py`
- `test_stats.py` のファイル内容が変更されていないこと。
