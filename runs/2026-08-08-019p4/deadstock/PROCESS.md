# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [x] **architect** → `design.md`
   - task: Analyze the CSV structures of inventory.csv, sales.csv, and returns.csv. Design the logic for calculating 'Net Sales' (純販売数) and the filtering process for 'Deadstock' (死に筋商品). Define the format for deadstock_report.txt.
   - 成功条件: Design document must specify how to handle products missing from sales.csv or returns.csv (default to 0) and the exact report structure.
2. [x] **implementer** → `deadstock_report.txt`
   - task: Develop a script to process inventory.csv, sales.csv, and returns.csv. Calculate net sales for each inventory item. Identify items with net sales <= 0. Generate deadstock_report.txt containing the header '死に筋商品リスト', the list of products with their net sales, and the criteria explanation.
   - 成功条件: The file must exist and contain '死に筋商品リスト' and '純販売数'.
   - 検査: `Get-Content deadstock_report.txt` → 「死に筋商品リスト」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that deadstock_report.txt exists, contains the required headings and terminology, and accurately lists products that meet the deadstock definition based on the source CSVs.
   - 成功条件: All SPEC criteria must be met: file existence, header presence, '純販売数' keyword, and correct product extraction. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
