# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
buggy_stats.py には複数のバグがある。test_stats.py を一切変更せずに、すべてのテストが通るように buggy_stats.py を修正してくれ。python test_stats.py の実行で OK が出ること。

## 操作的定義
- **すべてのテストが通る**: PowerShell上で `python test_stats.py` を実行した際、標準出力に `OK` という文字列が含まれ、かつ終了コードが 0 であること。

## 受入基準
1. [ ] test_stats.py が変更されていないこと（検査: `Get-Content test_stats.py`）
2. [ ] python test_stats.py を実行して OK が出力されること（検査: `python test_stats.py` → 出力に「OK」を含むこと）

## 仕様
### 目的
`buggy_stats.py` に含まれるバグを修正し、既存のテストスイート `test_stats.py` をすべてパスさせる。

### 制約
- `test_stats.py` は読み取り専用であり、一切の変更を禁止する。
- 修正は `buggy_stats.py` の内部のみで行う。

### 定義
- **すべてのテストが通る**: PowerShell上で `python test_stats.py` を実行した際、標準出力に `OK` という文字列が含まれ、かつ終了コードが 0 である状態を指す。

### 納品物
- 修正済みの `buggy_stats.py`

### 完了基準（検査方法）
1. **不変性の確認**: `test_stats.py` が変更されていないことを確認する。
2. **動作確認**: 以下のコマンドを実行し、出力に `OK` が含まれていることを確認する。
   - 実行コマンド: `python test_stats.py`
   - 期待される出力: `OK`
