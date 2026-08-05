# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: PowerShellで 'python test_stats.py' を実行し、標準出力に 'OK' という文字列が含まれている状態でプロセスが正常終了すること。

## 受入基準
- [ ] test_stats.py の全テストケースが合格し、OK が表示されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
- [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py` → 出力に「"""stats の仕様を定めるテスト。このファイルは変更禁止（読み取り専用）。"""」を含むこと）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` の全テストを合格させる。

【制約】
1. `test_stats.py` は一切変更してはならない。
2. 修正後の `buggy_stats.py` は、`python test_stats.py` を実行した際に標準出力に `OK` を出力しなければならない。

【実装詳細】
- `buggy_stats.py` 内の `mean`, `median`, `variance`, `value_range` 等の関数について、`test_stats.py` で期待されている動作（エッジケース、計算精度、例外処理など）に合わせてロジックを修正すること。

【検収基準】
- 実行コマンド: `python test_stats.py`
- 期待される出力: `OK` という文字列が含まれていること。
