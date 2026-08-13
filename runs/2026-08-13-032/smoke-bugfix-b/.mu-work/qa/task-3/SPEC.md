# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: コマンド `python test_stats.py` を実行し、標準出力に文字列 'OK' が含まれ、かつ終了コードが 0 であること
- **test_stats.py を一切変更しない**: ファイルのハッシュ値が、修正作業前後で同一であること

## 受入基準
1. [ ] buggy_stats.py が修正され、test_stats.py の全テストをパスして 'OK' と出力すること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
2. [ ] test_stats.py が変更されていないこと（検査: `(Get-FileHash test_stats.py).Hash`）

## 仕様
【目的】
`buggy_stats.py` に含まれるバグを修正し、`test_stats.py` による検証をすべてパスさせる。

【制約】
- `test_stats.py` は読み取り専用とし、一切の変更（コード修正、コメント追加、改行変更等）を禁止する。
- `buggy_stats.py` のみを修正して目的を達成すること。

【完了定義】
以下の基準をすべて満たしたとき、本タスクは完了とする。
1. `python test_stats.py` を実行した際、標準出力に 『OK』 という文字列が出力されること。
2. `python test_stats.py` の終了コードが 0 であること。
3. `test_stats.py` のファイル内容（ハッシュ値）が変更されていないこと。

【成果物】
- 修正済みの `buggy_stats.py`
