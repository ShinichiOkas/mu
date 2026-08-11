# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [ ] **researcher** → `report.md`
   - task: Research and compare the four local LLM backends (Ollama, llama.cpp, vLLM, LM Studio) across the five specified criteria: ease of setup, API compatibility, resource consumption, model deployment effort, and inference speed. For every technical claim or performance metric, find and record the official documentation or a reliable technical source URL. Analyze whether Ollama should be maintained as the foundation for 'mu' (a minimal general-purpose agent) based on these findings.
   - 成功条件: The report must cover all 4 tools, all 5 criteria, provide source URLs for every claim, and include a conclusion regarding Ollama's suitability for 'mu'.
   - 検査: `Get-Content report.md | Select-String -Pattern 'Ollama', 'llama.cpp', 'vLLM', 'LM Studio'` → 「Ollama」
2. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that report.md meets all specifications: existence of the file, presence of all 4 tools, coverage of all 5 criteria, inclusion of source URLs for all claims, and a clear conclusion on the usage of Ollama for 'mu'.
   - 成功条件: Confirmation that all SPEC criteria (including the mechanical ones and the qualitative ones like URL presence and conclusion quality) are satisfied. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Test-Path report.md` → 「True」
