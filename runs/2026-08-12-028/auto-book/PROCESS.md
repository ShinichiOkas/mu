# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
テーマ『修理』の掌編小説を書いてほしい。分量は800〜1200字。読者が結末で認識の反転（それまでの見え方が変わる驚き）を得られること。執筆と、編集者の指摘を受けた改稿を経た最終稿を story.md として納品すること。

## タスク列
1. [x] **writer** → `story_draft.md`
   - task: Create a plot outline and a first draft of a short story themed around 'Repair' (修理), ensuring a 'reversal of perception' (認識の反転) occurs at the end. Target length: 800-1200 characters.
   - 成功条件: The story must involve 'repair' and set up a twist for the reversal. Length should be approximately 800-1200 characters.
2. [x] **editor** → `editorial_notes.md`
   - task: Review the first draft (story_draft.md). Evaluate the strength of the 'reversal of perception', the consistency of the plot, and whether the character count is within the 800-1200 range. Provide specific improvement notes.
   - 成功条件: Notes must specifically address the reversal's impact, character count, and any logical inconsistencies.
3. [x] **writer** → `story.md`
   - task: Revise the story based on the editorial notes in editorial_notes.md to finalize the manuscript. Ensure the final version is between 800 and 1200 characters (excluding spaces/newlines) and incorporates the 'repair' theme and the 'reversal of perception'.
   - 成功条件: The final story must be 800-1200 characters and reflect the changes suggested in editorial_notes.md.
   - 検査: `(Get-Content story.md -Raw).Replace("`r`n", "").Replace("`n", "").Replace(" ", "").Length`
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the final deliverable against the SPEC. Check if story.md exists, the character count is between 800-1200, the word '修理' is present, the 'reversal of perception' is effective, and the revision process (draft -> notes -> final) was followed.
   - 成功条件: Independent verification of all criteria including the mechanical checks and the qualitative 'reversal' and 'process' requirements. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
