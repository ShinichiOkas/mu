# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the logic for calculating 'Actual Sales' (sales.csv sum - returns.csv sum) for each item in inventory.csv, identify 'Dead Stock' (Actual Sales <= 0), and define the report format for dead_stock_report.txt.
   - 成功条件: The design document must explicitly define the calculation formula and the filtering logic based on the SPEC.
2. [ ] **implementer** → `verify_logic.ps1`
   - task: Create a PowerShell verification script that reads dead_stock_report.txt and validates if the reported 'Dead Stock' items actually have Actual Sales <= 0 based on the input CSVs, ensuring the logic is correctly applied before the final report is accepted.
   - 成功条件: The script must output 'PASS' if the report's contents match the CSV data logic, and 'FAIL' otherwise.
3. [ ] **implementer** → `dead_stock_report.txt`
   - task: Process inventory.csv, sales.csv, and returns.csv to calculate actual sales. Identify items with actual sales <= 0 and generate dead_stock_report.txt containing the item name and the detailed breakdown (Sales X - Returns Y = Actual Z).
   - 成功条件: The file must exist and contain the required breakdown for dead stock items.
   - 検査: `Test-Path dead_stock_report.txt` → 「True」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the final report against the SPEC criteria: check for existence, presence of item names (e.g., 消しゴム), and the term '実質販売数'. Run the frozen verify_logic.ps1 to ensure data integrity.
   - 成功条件: The report must pass all SPEC criteria and the logic verification script. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Get-Content dead_stock_report.txt` → 「実質販売数」
