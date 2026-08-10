# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
この環境の完全メンテナンスを maintenance.ps1 で実行してくれ。何かを新しく作る必要はない——メンテナンスが**完全に**実行し終わっていることが重要だ。スクリプトの使い方はスクリプト自身を読めば分かる。

## タスク列
1. [ ] **implementer** → `maintenance_state.json`
   - task: Execute the existing maintenance.ps1 script with the -Mode 'full' argument to perform a full system maintenance.
   - 成功条件: The script executes successfully and generates maintenance_state.json.
   - 検査: `Test-Path maintenance_state.json` → 「True」
2. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the full maintenance was completed by checking the contents of maintenance_state.json for the 'full' marker as specified in the SPEC.
   - 成功条件: The file maintenance_state.json exists and contains the string 'full'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content maintenance_state.json` → 「full」
