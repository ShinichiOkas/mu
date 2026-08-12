# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: 春を詠んだ日本語の俳句を3句作成し、1行に1句、行頭を「- 」としてpoem_a.mdに保存してください。
   - 成功条件: poem_a.mdに「- 」で始まる行が3行存在すること
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: 秋を詠んだ日本語の俳句を3句作成し、1行に1句、行頭を「- 」としてpoem_b.mdに保存してください。
   - 成功条件: poem_b.mdに「- 」で始まる行が3行存在すること
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: poem_a.mdとpoem_b.mdの内容がSPEC（春と秋の俳句がそれぞれ3句、行頭が「- 」であること）を満たしているか検証し、結果をverdict.mdに記述してください。
   - needs: poem_a.md, poem_b.md
   - 成功条件: SPECの全基準を満たしているか判定され、最終的な合格/不合格が明記されていること / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
