# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the CSV structures (inventory, sales, returns) and design the logic to calculate 'Net Sales' (純販売数) and identify 'Deadstock' (死に筋商品). Define the format for deadstock_report.txt including the required criteria.
   - 成功条件: The design must explicitly define the formula (Net Sales = Total Sales - Total Returns) and the reporting structure required by the SPEC.
   - 検査: `Get-Content design.md` → 「純販売数」
2. [ ] **implementer** → `deadstock_report.txt`
   - task: Develop a script to process the CSV files, calculate the net sales per product, identify products with net sales <= 0, and generate the deadstock_report.txt file containing the criteria, list of products, and the breakdown of sales/returns/net sales.
   - 成功条件: The report must exist and contain the specific product P003 and the term '純販売数' based on the provided calculations.
   - 検査: `Get-Content deadstock_report.txt` → 「P003」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the deadstock_report.txt against all SPEC criteria: existence, inclusion of the determination criteria (純販売数 <= 0), presence of correctly identified deadstock products (like P003), and inclusion of the underlying figures (sales, returns, net sales).
   - 成功条件: All SPEC criteria must be marked as passed. The report must accurately reflect the calculations from the input CSVs. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
