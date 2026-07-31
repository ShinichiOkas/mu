# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design a Python script to calculate deadstock by reading inventory.csv, sales.csv, and returns.csv. The logic must filter data for the last 90 days, calculate Net Sales (Sales - Returns), and identify items where Net Sales equals 0. Specify the output format for deadstock_report.csv with columns [商品ID, 商品名, 正味販売数量].
   - 成功条件: Design must specify data joining logic (by Product ID) and the time-filtering mechanism.
2. [ ] **implementer** → `deadstock_report.csv`
   - task: Implement the Python script based on design.md. Read the three CSV files, filter the sales and returns records for the last 90 days relative to the latest date in the dataset, compute net sales per product, and export the deadstock list to deadstock_report.csv.
   - 成功条件: The generated CSV must contain only products with Net Sales = 0 and include the columns [商品ID, 商品名, 正味販売数量].
   - 検査: `Get-ChildItem deadstock_report.csv` → 「deadstock_report.csv」
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that deadstock_report.csv exists and contains the required 'Net Sales' (正味販売数量) column and that the data correctly identifies deadstock as defined in the SPEC.
   - 成功条件: Confirmation that the file exists and the header contains 'Net Sales' or '正味販売数量'.
   - 検査: `Get-Content deadstock_report.csv` → 「正味販売数量」
