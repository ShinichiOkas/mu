# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: 春を詠んだ日本語の俳句を3句作成し、各行の行頭を「- 」にして poem_a.md に保存してください。
   - 成功条件: poem_a.md に「- 」で始まる行が3行存在すること
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: 秋を詠んだ日本語の俳句を3句作成し、各行の行頭を「- 」にして poem_b.md に保存してください。
   - 成功条件: poem_b.md に「- 」で始まる行が3行存在すること
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: poem_a.md と poem_b.md の内容を確認し、それぞれ春と秋の俳句が3句ずつ、「- 」で始まる形式で正しく記述されているかを検証し、最終的な判定を verdict.md に記述してください。
   - needs: poem_a.md, poem_b.md
   - 成功条件: SPECのすべての条件（春/秋の書き分け、3句ずつ、行頭記号）が満たされていること / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
