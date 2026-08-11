# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design the logic for identifying 'deadstock' items. Define the data processing flow: load inventory.csv for the master list, aggregate quantities from sales.csv and returns.csv per product code, calculate net sales quantity (Net = Sales - Returns), and filter those <= 0. Specify the format for deadstock_report.txt.
   - 成功条件: The design document clearly defines the calculation formula and the output report structure.
   - 検査: `Get-Content design.md` → 「純売上数量」
2. [ ] **implementer** → `analyze_deadstock.py`
   - task: Develop a Python script to process inventory.csv, sales.csv, and returns.csv according to the design. The script must identify items with net sales quantity <= 0 and write a report named 'deadstock_report.txt' containing the header '死に筋商品リスト', and for each item: product code, name, and the calculated '純売上数量'.
   - 成功条件: The script runs without error and produces deadstock_report.txt.
   - 検査: `python analyze_deadstock.py` → 「True」
3. [ ] **implementer** → `deadstock_report.txt`
   - task: Execute the analysis script to generate the final report.
   - 成功条件: The report file is created and contains the required header and metric label.
   - 検査: `Get-Content deadstock_report.txt` → 「死に筋商品リスト」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the deliverables against the SPEC. 1. Check for existence of deadstock_report.txt. 2. Verify '死に筋商品リスト' and '純売上数量' are present. 3. Manually verify that all product codes from inventory.csv were considered in the calculation logic (via script review or output check).
   - 成功条件: All acceptance criteria in the SPEC are met. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
