# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
テーマ『修理』の掌編小説を書いてほしい。分量は800〜1200字。読者が結末で認識の反転（それまでの見え方が変わる驚き）を得られること。執筆と、編集者の指摘を受けた改稿を経た最終稿を story.md として納品すること。

## タスク列
1. [x] **writer** → `outline.md`
   - task: Create a plot outline for a flash fiction story themed around 'Repair' (修理), ensuring a structure that leads to a 'perception flip' (認識の反転) at the conclusion. The final target length is 800-1200 characters.
   - 成功条件: The outline must clearly define the initial premise, the 'repair' element, and the specific twist that flips the reader's perception.
2. [x] **writer** → `story_draft.md`
   - task: Write the first draft of the story based on the outline. The text must be between 800 and 1200 characters (including spaces/newlines) as measured by (Get-Content story_draft.md -Raw).Length.
   - 成功条件: The story must include the theme of 'repair' and implement the perception flip. Length must be 800-1200 characters.
   - 検査: `$len = (Get-Content story_draft.md -Raw).Length; if ($len -ge 800 -and $len -le 1200) { 'Pass' } else { "Fail: $len" }` → 「Pass」
3. [x] **editor** → `review_notes.md`
   - task: Review story_draft.md for narrative coherence, the effectiveness of the 'perception flip', and adherence to the theme of 'repair'. Provide specific feedback and suggestions for improvement.
   - 成功条件: The review must provide substantive critique on whether the twist is surprising and if the 'repair' theme is central.
4. [ ] **writer** → `story.md`
   - task: Revise the story based on the review_notes.md. The final version must be saved as story.md and maintain a length of 800-1200 characters.
   - 成功条件: The final manuscript must incorporate the editor's feedback and satisfy the length requirement.
   - 検査: `$len = (Get-Content story.md -Raw).Length; if ($len -ge 800 -and $len -le 1200) { 'Pass' } else { "Fail: $len" }` → 「Pass」
5. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that story.md meets all SPEC requirements: 1. File exists. 2. Length is 800-1200 characters. 3. Contains '修理' or repair concepts. 4. Successfully implements a 'perception flip' in the ending.
   - 成功条件: The verdict must explicitly confirm all criteria from the SPEC are met. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Test-Path story.md` → 「True」
