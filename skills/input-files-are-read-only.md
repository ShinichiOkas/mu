---
description: 入力として挙げられたファイルを書き換えない（テストデータが要るなら別名の一時ファイル）
applies_to: implementer
maturity: confirmed
origin: roles/*/implementer.md から移行（合意029）。文面は実走で調整済み
---
- **入力ファイルは読み取り専用**。仕様・設計が入力として挙げるファイルを上書き・編集・削除しない。
  テストデータが必要なら別名の一時ファイルを作り、最後に削除する。
