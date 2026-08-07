# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the data processing logic for calculating net sales and identifying dead stock items based on the provided definitions. Specify the format of the final report (dead_stock_report.txt) to ensure it includes item names, stock levels, net sales, and the specific reason for classification.
   - 成功条件: The design document must clearly map the input CSVs to the net sales calculation and the two conditional paths for dead stock identification.
2. [ ] **implementer** → `dead_stock_report.txt`
   - task: Develop a script to process inventory.csv, sales.csv, and returns.csv. Calculate net sales per product, apply the dead stock criteria, and generate the report file 'dead_stock_report.txt' containing the required details and reasons.
   - 成功条件: The report must exist and include P003 with its net sales and stock count, as per the provided test data constraints.
   - 検査: `Get-Content dead_stock_report.txt` → 「P003」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the dead_stock_report.txt exists, contains product P003, and explicitly mentions the reasoning based on '正味販売数' or inventory levels as per the SPEC.
   - 成功条件: All three acceptance criteria in the SPEC must be verified as True/Present. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Test-Path dead_stock_report.txt` → 「True」
