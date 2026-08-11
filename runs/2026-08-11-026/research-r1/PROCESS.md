# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [ ] **researcher** → `research_notes.md`
   - task: Investigate the four local LLM execution frameworks (Ollama, llama.cpp, vLLM, LM Studio) focusing on the five specific criteria: setup cost, resource consumption, API compatibility, model management ease, and inference speed. Gather source URLs for every claim.
   - 成功条件: The file contains detailed findings for all 4 tools across all 5 criteria, with corresponding URLs for each claim.
   - 検査: `Get-Content research_notes.md | Select-String 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio'`
2. [ ] **implementer** → `report.md`
   - task: Create the final report (report.md) based on research_notes.md. The report must include a comparison of the 4 tools against the 5 criteria, cite URLs for all claims, and provide a definitive conclusion on whether to continue using Ollama for the 'mu' agent based on the 'minimal' design philosophy.
   - 成功条件: The report contains mentions of all 4 tools, all 5 criteria, includes URLs for all claims, and has a clear conclusion section.
   - 検査: `Get-Content report.md | Select-String 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio', 'セットアップコスト', 'リソース消費量', 'APIの互換性', 'モデル管理の容易さ', '推論速度', '結論'`
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that report.md meets all criteria in the SPEC: existence of the file, coverage of 4 tools, coverage of 5 specific criteria, presence of source URLs for every claim, and a clear conclusion regarding Ollama.
   - 成功条件: The verdict.md file explicitly states 'PASS' or 'FAIL' based on the SPEC criteria. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
