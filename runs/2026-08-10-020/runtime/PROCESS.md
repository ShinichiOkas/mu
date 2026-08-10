# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the structure of the 'comparison_report.md' based on the SPEC. Define the comparison matrix columns (setup difficulty, resource consumption, API compatibility, model formats, throughput, primary use case) and the logical flow from analysis to conclusion regarding Ollama's suitability for 'mu'.
   - 成功条件: The design document outlines all required sections: comparison table, detailed analysis for minimal agents, final conclusion, and evidence placement.
   - 検査: `Get-Content design.md | Select-String -Pattern 'comparison table', 'conclusion'` → 「comparison table」
2. [ ] **implementer** → `comparison_report.md`
   - task: Research the four LLM execution platforms (Ollama, llama.cpp, vLLM, LM Studio) and create 'comparison_report.md'. Ensure the report contains a comparison table, a detailed analysis of 'mu's' critical needs, a clear Yes/No/Conditional conclusion on continuing with Ollama, and source URLs for all claims.
   - 成功条件: The report contains all 4 tool names, keywords 'リソース消費量' and 'セットアップ', at least one URL, and a clear conclusion on Ollama.
   - 検査: `Get-Content comparison_report.md | Select-String -Pattern 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio', 'リソース消費量', 'セットアップ', 'https?://'` → 「Ollama」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Independently verify 'comparison_report.md' against the SPEC. Confirm that the conclusion is explicit and the evidence is grounded in provided URLs. Check that the 'mu' suitability criteria (setup, resources, extensibility) are addressed.
   - 成功条件: Verdict must state 'PASS' or 'FAIL' based on the SPEC's acceptance criteria. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md | Select-String -Pattern 'PASS', 'FAIL'` → 「PASS」
