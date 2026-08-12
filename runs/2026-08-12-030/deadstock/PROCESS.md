# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [x] **architect** → `design.md`
   - task: Create design document for identifying deadstock items from CSV inputs.
   - 成功条件: The document must outline the logic to merge inventory, sales, and returns data based on product codes.
   - 検査: `Test-Path design.md` → 「True」
2. [ ] **implementer** → `deadstock_report.txt`
   - task: Analyze CSV files and generate the deadstock report.
   - needs: design.md, inventory.csv, sales.csv, returns.csv
   - 成功条件: Report must include product codes, counts, and specific reasoning for items meeting 'Deadstock' criteria.
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify report contents against requirements.
   - needs: design.md, deadstock_report.txt
   - 成功条件: The verdict must confirm all requirements are met based on the check commands. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
