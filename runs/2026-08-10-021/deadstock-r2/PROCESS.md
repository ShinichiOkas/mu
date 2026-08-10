# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the input CSV structures (inventory, sales, returns) and design the logic for calculating 'Net Sales Volume' and identifying 'Deadstock' based on the provided definitions. Define the report format for deadstock_report.txt.
   - 成功条件: The design document must clearly map the CSV columns to the net sales calculation and the specific conditions for deadstock identification.
2. [ ] **implementer** → `generate_report.ps1`
   - task: Write a PowerShell script to process the CSV files, calculate net sales for each product, identify deadstock products, and generate the 'deadstock_report.txt' file according to the design. Ensure the report includes the heading '死に筋商品一覧' and the basis for judgment including '純販売数量'.
   - 成功条件: The script must execute without errors and produce the report based on the provided CSV files.
3. [ ] **implementer** → `deadstock_report.txt`
   - task: Execute the generate_report.ps1 script to produce the final report.
   - 成功条件: The report file must exist and contain the required keywords.
   - 検査: `Get-Content deadstock_report.txt` → 「死に筋商品一覧」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the 'deadstock_report.txt' fulfills all SPEC requirements: presence of the file, inclusion of the specific heading '死に筋商品一覧', and the listing of products with their net sales volume as the basis for judgment.
   - 成功条件: The verdict must confirm all SPEC criteria are met: file existence, specific heading presence, and quantitative evidence (純販売数量) for each item. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
