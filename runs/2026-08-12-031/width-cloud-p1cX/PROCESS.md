# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: Create poem_a.md containing 3 Japanese haiku about spring, each on a new line starting with '- '.
   - 成功条件: The file contains exactly 3 lines, each starting with '- ' and depicting spring.
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: Create poem_b.md containing 3 Japanese haiku about autumn, each on a new line starting with '- '.
   - 成功条件: The file contains exactly 3 lines, each starting with '- ' and depicting autumn.
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa**（model: gemma4:31b-cloud） → `verdict.md`
   - task: Verify that both poem_a.md and poem_b.md strictly follow the specification (3 haiku per file, starting with '- ', correct themes).
   - needs: poem_a.md, poem_b.md
   - 成功条件: The verdict.md file states 'PASS' if both poems meet all criteria, otherwise 'FAIL'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
