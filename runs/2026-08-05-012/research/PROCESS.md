# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design the structure of the comparison report. Define the specific evaluation criteria for 'ease of setup', 'API compatibility', 'resource consumption', and 'model deployment cost' for Ollama, llama.cpp, vLLM, and LM Studio. Outline the logic for the conclusion regarding mu's requirements.
   - 成功条件: The design must cover all 4 tools and 4 required perspectives, and define how the conclusion will be derived based on mu's minimal agent nature.
   - 検査: `Get-Content design.md` → 「Ollama」
2. [ ] **implementer** → `report.md`
   - task: Conduct research on the four tools and draft the report.md. Create the comparison table, detailed analysis, and final conclusion. Ensure every technical claim is backed by a real, valid URL. Implement a accompanying check_sources.py script that parses URLs from report.md and validates them via HTTP requests, outputting 'ALL_URLS_VALID' on success.
   - 成功条件: Must include the comparison table, detailed analysis, and conclusion. report.md must contain valid URLs and the script check_sources.py must exist and pass.
   - 検査: `python check_sources.py` → 「ALL_URLS_VALID」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that report.md meets all SPEC requirements: contains all 4 tools, addresses all 4 defined perspectives, reaches a clear conclusion about Ollama, and that all URLs are actually valid via check_sources.py.
   - 成功条件: Independent verification of tool coverage, perspective coverage, conclusion existence, and URL validity. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
   - 検査: `Get-Content verdict.md` → 「PASSED」
