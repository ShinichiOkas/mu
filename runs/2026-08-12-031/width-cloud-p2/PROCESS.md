# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: Create poem_a.md containing 3 Japanese haikus about spring, each on a new line starting with '- '.
   - 成功条件: The file contains exactly 3 lines, and each line starts with '- '.
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: Create poem_b.md containing 3 Japanese haikus about autumn, each on a new line starting with '- '.
   - 成功条件: The file contains exactly 3 lines, and each line starts with '- '.
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa**（model: gemma4:31b-cloud） → `verdict.md`
   - task: Verify that poem_a.md contains 3 spring haikus and poem_b.md contains 3 autumn haikus, both adhering to the required format ('- ' at the start of each line).
   - needs: poem_a.md, poem_b.md
   - 成功条件: Both files exist and meet the formatting and thematic requirements specified in the SPEC. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
