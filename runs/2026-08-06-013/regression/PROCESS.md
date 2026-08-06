# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Define the logic for calculating net sales and identifying dead stock products based on the provided CSV files. Design the structure of the verification script and the final report.
   - 成功条件: The design must clearly define the formula for 'Net Sales' and the condition for 'Dead Stock Product' as per the SPEC.
2. [ ] **implementer** → `verifier.py`
   - task: Create a Python verification script that will be used to validate the final report. The script should read the CSV files, calculate the expected dead stock products, and then check if 'dead_stock_report.txt' contains the correct products and their supporting data (net sales and inventory).
   - 成功条件: The script must print 'PASS' if the report is correct and 'FAIL' otherwise.
3. [ ] **implementer** → `dead_stock_report.txt`
   - task: Implement the data processing logic to identify dead stock products from inventory.csv, sales.csv, and returns.csv, and generate the final report 'dead_stock_report.txt' including product codes, names, net sales, and inventory counts.
   - 成功条件: The report must list all products meeting the dead stock criteria with their supporting numbers.
   - 検査: `python verifier.py` → 「PASS」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the final deliverable 'dead_stock_report.txt' exists and contains the required string '純売上数', and that the business logic defined in the SPEC was strictly followed.
   - 成功条件: Verification result must be 'PASS' if both the file exists and contains the keyword. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Get-Content dead_stock_report.txt` → 「純売上数」
