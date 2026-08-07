# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design the structure of the comparison report (report.md). Define the comparison matrix based on the 4 tools (Ollama, llama.cpp, vLLM, LM Studio) and 4 perspectives (Setup, Resource, API, Performance). Map out how the 'minimal agent (mu)' context will be applied to the analysis and define the logic for the final conclusion.
   - 成功条件: The design document must include a table structure for comparison and a section for the 'mu' context analysis.
   - 検査: `Get-Content design.md | Select-String 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio'` → 「Ollama」
2. [ ] **implementer** → `report.md`
   - task: Research and write the local LLM comparison report. For each tool (Ollama, llama.cpp, vLLM, LM Studio), provide quantitative/qualitative data on setup ease, resource usage, API compatibility, and performance. Include absolute URLs for every claim. Analyze these in the context of the 'mu' project and conclude whether to continue with Ollama or migrate.
   - 成功条件: The report must contain all 4 tools, all 4 perspectives, source URLs, and a final conclusion regarding Ollama's validity for 'mu'.
   - 検査: `Get-Content report.md | Select-String 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio', 'セットアップ', 'リソース消費量', 'API互換性', '推論パフォーマンス', 'http'` → 「Ollama」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify report.md against the SPEC. Ensure all 4 tools are mentioned, all 4 perspectives are analyzed, absolute URLs are present, and the conclusion is logically derived from the provided data in the context of the 'mu' agent.
   - 成功条件: A clear 'PASS' or 'FAIL' must be stated based on the SPEC criteria. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Get-Content verdict.md | Select-String 'PASS', 'FAIL'` → 「PASS」
