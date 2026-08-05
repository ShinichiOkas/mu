# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the CSV structures of inventory.csv, sales.csv, and returns.csv to design the logic for calculating net sales and identifying deadstock products based on the specified criteria. Define the output format for deadstock_report.txt.
   - 成功条件: The design must explicitly map how to calculate 'Net Sales' and the conditional logic for 'Deadstock' (Net Sales <= 0 OR (Inventory > 0 AND Net Sales < 10)).
   - 検査: `Get-ChildItem design.md` → 「design.md」
2. [ ] **implementer** → `deadstock_report.txt`
   - task: Implement a script to process inventory.csv, sales.csv, and returns.csv. Calculate net sales per product code and generate deadstock_report.txt containing Product Code, Product Name, Inventory, Net Sales, and the Reason for judgment in UTF-8 encoding.
   - 成功条件: The report must contain all deadstock items as defined in the spec, including the specific numerical evidence (Net Sales and Inventory).
   - 検査: `Get-Content deadstock_report.txt` → 「純売上数」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that deadstock_report.txt exists and contains the expected data fields and correct deadstock identification based on the provided SPEC.
   - 成功条件: Confirm that the final report matches the SPEC requirements: it exists, uses UTF-8, and lists products meeting the deadstock criteria with their justification.
   - 検査: `Get-ChildItem deadstock_report.txt` → 「deadstock_report.txt」
