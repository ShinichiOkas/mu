# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的


## タスク列
1. [ ] **implementer** → `poem_a.md`
   - task: Create 3 spring haikus in poem_a.md with '- ' prefix.
   - 成功条件: Get-Content poem_a.md contains three lines starting with '- '
   - 検査: `Get-Content poem_a.md` → 「- 」
2. [ ] **implementer** → `poem_b.md`
   - task: Create 3 autumn haikus in poem_b.md with '- ' prefix.
   - 成功条件: Get-Content poem_b.md contains three lines starting with '- '
   - 検査: `Get-Content poem_b.md` → 「- 」
3. [ ] **qa** → `verdict.md`
   - task: Verify both poems meet the content and format requirements.
   - needs: poem_a.md, poem_b.md
   - 成功条件: Verify that poem_a.md contains spring haikus and poem_b.md contains autumn haikus, both with 3 lines starting with '- '. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
