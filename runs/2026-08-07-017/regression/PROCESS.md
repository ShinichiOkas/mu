# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the input CSV structures (inventory, sales, returns) and design the logic to calculate net sales (pure sales) and identify dead stock. Define the output format for dead_stock_report.txt including the required evidence strings.
   - 成功条件: The design document must specify the calculation formula and the report layout containing item code, item name, and the calculation basis.
   - 検査: `Get-Content design.md` → 「純販売数」
2. [ ] **implementer** → `analyze_stock.ps1`
   - task: Develop a script (PowerShell or Python) that reads inventory.csv, sales.csv, and returns.csv, calculates the net sales for each item in inventory, filters those with net sales <= 0, and generates the dead_stock_report.txt as specified in the design.
   - 成功条件: The script must execute without error and produce a file named dead_stock_report.txt.
   - 検査: `powershell -File analyze_stock.ps1` → 「True」
3. [ ] **implementer** → `dead_stock_report.txt`
   - task: Run the analysis script to generate the final report based on the provided data files.
   - 成功条件: The report must exist and contain the specific item P003 and the phrase '純販売数' as per the SPEC criteria.
   - 検査: `Get-Content dead_stock_report.txt` → 「P003」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that dead_stock_report.txt accurately lists dead stock items based on the provided CSVs and that the calculation evidence is explicitly stated for each item.
   - 成功条件: Verify that the report is present and contains both 'P003' and '純販売数'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む
   - 検査: `Get-Content dead_stock_report.txt` → 「純販売数」
