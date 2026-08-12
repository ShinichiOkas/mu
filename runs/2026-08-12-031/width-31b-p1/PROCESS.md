# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: Write 3 Japanese haikus about spring. Each haiku must be on a single line starting with '- '.
   - 成功条件: The file contains 3 lines, each starting with '- '.
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: Write 3 Japanese haikus about autumn. Each haiku must be on a single line starting with '- '.
   - 成功条件: The file contains 3 lines, each starting with '- '.
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that poem_a.md contains 3 spring haikus and poem_b.md contains 3 autumn haikus, both adhering to the format (3 lines starting with '- ').
   - needs: poem_a.md, poem_b.md
   - 成功条件: Confirmation that both files meet the spec requirements. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
