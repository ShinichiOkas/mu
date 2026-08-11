# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
この売上表 sales.csv から不採算商品を特定してくれ。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Define the data processing logic for calculating gross profit margin from sales.csv and the filtering criteria (< 15%) to identify unprofitable products. Specify the output format for unprofitable_products.txt.
   - 成功条件: The design document must explicitly state the formula (Price - Cost) / Price and the threshold 0.15.
   - 検査: `Get-Content design.md` → 「0.15」
2. [ ] **implementer** → `extract_unprofitable.ps1`
   - task: Create a PowerShell script to read sales.csv, calculate the gross profit margin for each item, filter those below 15%, and write the resulting product names to unprofitable_products.txt.
   - 成功条件: The script must correctly process sales.csv and produce unprofitable_products.txt.
   - 検査: `powershell -File extract_unprofitable.ps1`
3. [ ] **implementer** → `unprofitable_products.txt`
   - task: Execute the extraction script to generate the final list of unprofitable products.
   - 成功条件: The file must exist and contain product names that meet the criteria or a 'no target' message.
   - 検査: `Test-Path unprofitable_products.txt` → 「True」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the items in unprofitable_products.txt actually have a gross profit margin of less than 15% based on the data in sales.csv, and ensure no product with >= 15% is included.
   - 成功条件: The verification must confirm the mathematical correctness of the extracted list against the source CSV. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
