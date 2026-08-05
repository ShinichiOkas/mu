# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
在庫表 inventory.csv・売上履歴 sales.csv・返品履歴 returns.csv から、死に筋商品を特定して報告書を作ってくれ。なぜ死に筋と判定したかも分かるようにして。

## タスク列
1. [x] **developer**（model: gemma4:31b-cloud） → `analyze_deadstock.ps1`
   - task: Create a script to identify deadstock products by calculating net sales (Total Sales - Total Returns) from inventory.csv, sales.csv, and returns.csv, and output the findings to report.txt.
   - 成功条件: Net sales are correctly calculated for each product and those with 10 or fewer net sales are listed in report.txt with their product name and code.
   - 検査: `powershell -ExecutionPolicy Bypass -File analyze_deadstock.ps1; Get-Content report.txt` → 「A report containing product names, codes, and net sales counts for items with net sales <= 10.」
2. [ ] **qa** → `verdict.md`
   - task: 受け入れ基準に照らして成果物を独立に検証し、判定書を書く
   - 成功条件: 判定書の1行目が『ACHIEVED: 』で始まる
