# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [x] **architect** → `design.md`
   - task: Analyze the input CSV files (inventory.csv, sales.csv, returns.csv) and design the logic to calculate net sales (Total Sales - Total Returns) for each product in inventory. Define the structure of the final report (deadstock_report.txt) including the criteria and the list of products with net sales <= 0.
   - 成功条件: The design document must explicitly define the calculation formula for '純売上数' and the filtering condition for '死に筋商品'.
   - 検査: `Get-Content design.md` → 「純売上数」
2. [x] **implementer** → `analyze_deadstock.ps1`
   - task: Write a PowerShell script to process the CSV files based on design.md. The script must: 1. Read inventory.csv. 2. Aggregate quantities from sales.csv and returns.csv per product. 3. Calculate net sales. 4. Identify products with net sales <= 0. 5. Generate deadstock_report.txt containing the calculation method and the list of deadstock products (code, name, net sales).
   - 成功条件: The script must execute without error and produce deadstock_report.txt.
   - 検査: `powershell -File .\analyze_deadstock.ps1; Test-Path deadstock_report.txt` → 「True」
3. [ ] **implementer** → `deadstock_report.txt`
   - task: Execute the analysis script to generate the final report.
   - 成功条件: The report must exist and contain the term '純売上数' and the specific deadstock item 'P003' (as per SPEC criteria).
   - 検査: `Get-Content deadstock_report.txt` → 「P003」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the final deliverable (deadstock_report.txt) against the SPEC. Ensure the calculation logic for '純売上数' is stated, and all products from inventory.csv with net sales <= 0 are correctly listed.
   - 成功条件: The verdict must explicitly state 'PASS' if all SPEC criteria are met, otherwise 'FAIL'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む
   - 検査: `Get-Content verdict.md` → 「PASS」
