# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the logic for calculating net sales (real sales) and identifying deadstock items based on the provided CSV files. Define the data processing steps and the format of the final report.
   - 成功条件: The design must clearly define how to handle products missing from sales.csv and how to calculate '実質販売数' using the three CSV files.
2. [ ] **implementer** → `deadstock_report.txt`
   - task: Implement a script to process inventory.csv, sales.csv, and returns.csv. Calculate the net sales for each item in inventory. Identify deadstock items (net sales <= 0 or not present in sales.csv) and generate deadstock_report.txt in UTF-8 format including item codes, names, and the reasoning (net sales count).
   - 成功条件: The file deadstock_report.txt must contain a list of deadstock products and their corresponding net sales values.
   - 検査: `Get-Content deadstock_report.txt` → 「実質販売数」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that deadstock_report.txt exists and contains the required information (deadstock items and their net sales reasoning) as per the SPEC.
   - 成功条件: Verify that the report file exists and the content includes the term '実質販売数' and correct product details.
   - 検査: `Test-Path deadstock_report.txt` → 「True」
