# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the logic for calculating net sales across inventory.csv, sales.csv, and returns.csv using case-insensitive matching. Define the output format for deadstock_report.txt and the data processing steps.
   - 成功条件: The design must explicitly address case-insensitive matching and the formula for 'Net Sales' (sales - returns) filtered by presence in inventory.csv.
2. [ ] **implementer** → `analyzer.ps1`
   - task: Create a script (PowerShell or Python) that reads inventory.csv, sales.csv, and returns.csv, calculates net sales per item (case-insensitive), identifies items with net sales <= 0, and writes the results to deadstock_report.txt according to the spec requirements.
   - 成功条件: The script must produce deadstock_report.txt containing the item code, item name, and net sales for all deadstock items, or a message stating none were found.
3. [ ] **implementer** → `deadstock_report.txt`
   - task: Execute the analyzer.ps1 script to generate the final report.
   - 成功条件: The file deadstock_report.txt must be created and non-empty.
   - 検査: `Test-Path deadstock_report.txt` → 「True」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify deadstock_report.txt against the SPEC. Ensure it lists the product code, product name, and net sales for deadstock items (net sales <= 0) and that the logic adheres to case-insensitive matching. If no deadstock exists, verify the appropriate message is present.
   - 成功条件: The report must accurately reflect the data in the input CSVs based on the defined rules. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
