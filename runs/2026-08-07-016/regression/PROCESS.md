# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Define the logic for calculating 'net sales quantity' and identifying 'dead stock' based on the three CSV files, and design the format for dead_stock_report.txt.
   - 成功条件: The design document must explicitly define the aggregation logic for sales/returns and the conditional logic for dead stock classification.
   - 検査: `Get-Content design.md` → 「正味販売数量」
2. [ ] **implementer** → `dead_stock_report.txt`
   - task: Write a script to process inventory.csv, sales.csv, and returns.csv to identify dead stock products and generate dead_stock_report.txt following the design.md specification.
   - 成功条件: The report must list all dead stock products with their corresponding net sales quantity and inventory count as evidence.
   - 検査: `Get-Content dead_stock_report.txt` → 「P003」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that dead_stock_report.txt exists, contains the expected product codes, and provides the numerical evidence (net sales and inventory) for each item as required by the SPEC.
   - 成功条件: Verification must confirm the existence of the file and the presence of quantitative evidence for the dead stock classification. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Test-Path dead_stock_report.txt` → 「True」
