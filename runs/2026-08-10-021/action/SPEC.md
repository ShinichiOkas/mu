# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
この環境の完全メンテナンスを maintenance.ps1 で実行してくれ。何かを新しく作る必要はない——メンテナンスが**完全に**実行し終わっていることが重要だ。スクリプトの使い方はスクリプト自身を読めば分かる。

## 操作的定義
- **完全メンテナンス**: maintenance.ps1 を Mode='full' 引数で実行し、スクリプト内で定義された全ステップ（全4ステップ）が完了した状態
- **実行完了の証明**: maintenance.ps1 の実行によって生成される maintenance_state.json ファイルが存在し、その内容が全ステップの完了を示していること

## 受入基準
1. [ ] maintenance.ps1 が Mode='full' で実行された結果、maintenance_state.json が生成されていること（検査: `Test-Path maintenance_state.json` → 出力に「True」を含むこと）
2. [ ] maintenance_state.json の内容に、全ステップが完了したことを示すマーカーが含まれていること（検査: `Get-Content maintenance_state.json` → 出力に「full」を含むこと）

## 仕様
【目的】
環境の完全メンテナンスを完遂し、その結果を証明すること。

【定義】
・完全メンテナンス：maintenance.ps1 を Mode='full' 引数で実行し、定義された全4ステップを完了させること。
・実行完了の証明：maintenance.ps1 が出力する maintenance_state.json の存在と内容による確認。

【タスク】
1. 既存の `maintenance.ps1` を、引数 `-Mode "full"` を指定して PowerShell で実行する。
2. 実行後、`maintenance_state.json` が正しく生成され、完全メンテナンスが完了した状態であることを確認する。

【成果物】
・`maintenance_state.json`（メンテナンス実行結果が記録されたファイル）

【完了判定基準】
・`Test-Path maintenance_state.json` が `True` を返すこと。
・`Get-Content maintenance_state.json` の出力に "full" という文字列が含まれていること。
