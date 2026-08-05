# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the logic to calculate net sales volume by aggregating sales.csv and returns.csv for each item in inventory.csv, and filter items where net sales <= 0. Define the format for report.txt including the mandatory '実質売上数量' marker.
   - 成功条件: The design must clearly map the input CSVs to the output report.txt and specify the subtraction logic (Sales Sum - Returns Sum).
2. [ ] **implementer** → `report.txt`
   - task: Create a script to process inventory.csv, sales.csv, and returns.csv. Calculate the net sales volume for each item. Identify 'dead stock' (net sales <= 0) and generate report.txt listing product code, name, and net sales volume.
   - 成功条件: report.txt must contain a list of dead stock items with their respective '実質売上数量'.
   - 検査: `Get-ChildItem report.txt` → 「report.txt」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that report.txt exists and contains the required information and the marker '実質売上数量' as specified in the SPEC.
   - 成功条件: The report must be present and contain the text '実質売上数量'. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Get-Content report.txt` → 「実質売上数量」
