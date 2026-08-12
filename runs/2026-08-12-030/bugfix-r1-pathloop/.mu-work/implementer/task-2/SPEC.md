# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: コマンド `python test_stats.py` を実行した際に、標準出力に 'OK' という文字列が含まれ、かつ終了コードが 0 で終了すること。

## 受入基準
1. [ ] test_stats.py が正常に完了し、成否を示す OK が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）
2. [ ] 元のファイル test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py | Measure-Object | Select-Object -ExpandProperty Count`）

## 仕様
目的：
`buggy_stats.py` 内のバグを修正し、`test_stats.py` を変更せずにすべてのテストをパスさせる。

定義：
- 「すべて通る」とは、`python test_stats.py` を実行した際に 'OK' という文字列が出力され、プロセスが正常終了することを指す。

詳細仕様：
1. `test_stats.py` の内容を解析し、要求されている統計機能の仕様（計算式、境界条件、型など）を確認すること。
2. `buggy_stats.py` を修正する。この際、`test_stats.py` が参照している関数やクラスのインターフェースは維持しつつ、内部ロジックを修正する。
3. 修正後の `buggy_stats.py` を用いて `python test_stats.py` を実行した際に、以下の条件を満たすこと：
    - 出力に 'OK' が含まれること。
    - `test_stats.py` 自体には一切の変更を加えないこと。
