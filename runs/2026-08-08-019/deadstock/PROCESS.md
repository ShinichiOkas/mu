# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Define the logic for calculating net sales (total sales - total returns) per product from the provided CSVs and the format for the final report. Document the data flow and calculation steps.
   - 成功条件: The design must explicitly state how to handle products with no sales or returns (as 0) and define the structure of deadstock_report.txt.
2. [ ] **implementer** → `deadstock_report.txt`
   - task: Create a script to analyze inventory.csv, sales.csv, and returns.csv, calculate net sales for all products, and generate deadstock_report.txt containing the list of deadstock products and their net sales values.
   - 成功条件: The report must include '死に筋商品', '正味販売数', and must list all products from inventory.csv (including P004).
   - 検査: `Get-Content deadstock_report.txt` → 「P004」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that deadstock_report.txt exists and contains the required headers and all inventory items as per the SPEC.
   - 成功条件: Verify the file existence, the presence of terms '死に筋商品' and '正味販売数', and that P004 is mentioned. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
