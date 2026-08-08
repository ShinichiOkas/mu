# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the CSV structures of inventory.csv, sales.csv, and returns.csv. Design the logic for calculating 'Net Sales Quantity' (sum of sales minus sum of returns) and identifying 'Deadstock Products' (present in inventory and net sales <= 0). Define the layout of deadstock_report.txt including the required sections '死に筋商品一覧' and '判定理由'.
   - 成功条件: Design document specifies the calculation logic, filter criteria, and the exact report structure required by the SPEC.
2. [ ] **implementer** → `generate_report.ps1`
   - task: Write a script to process the CSV files according to design.md. The script must: 1. Read inventory.csv, sales.csv, and returns.csv. 2. Calculate Net Sales Quantity for each item. 3. Identify items in inventory with Net Sales Quantity <= 0. 4. Generate deadstock_report.txt with '死に筋商品一覧' and '判定理由' sections.
   - 成功条件: The script executes without errors and produces deadstock_report.txt.
3. [ ] **implementer** → `deadstock_report.txt`
   - task: Execute the report generation script to produce the final deliverable.
   - 成功条件: The report file is created and contains the required headings.
   - 検査: `Get-Content deadstock_report.txt` → 「死に筋商品一覧」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the deadstock_report.txt against the SPEC. Ensure that: 1. The file exists. 2. It contains both '死に筋商品一覧' and '判定理由' headings. 3. The logic for 'Net Sales Quantity <= 0' is correctly applied to the products listed in the report based on the provided CSV data.
   - 成功条件: Final verdict confirms all criteria in the SPEC are met. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
