# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Define the structure of the comparison report (report.md), including a matrix for the 5 specified viewpoints (Resource usage, Setup ease, API compatibility, Inference speed, Model flexibility) and a logic flow for the final judgment on whether to continue using Ollama for 'mu'.
   - 成功条件: The design document must specify the layout for comparing Ollama, llama.cpp, vLLM, and LM Studio, and list the 5 required evaluation criteria.
2. [x] **implementer** → `verifier.ps1`
   - task: Create a PowerShell script that validates the existence of report.md and checks for the presence of 4 tool names, the 5 required viewpoints, at least one URL (http), and the keyword '判断' (judgment).
   - 成功条件: The script must print 'PASS' if all SPEC criteria are met in report.md, and 'FAIL' otherwise.
3. [ ] **implementer** → `report.md`
   - task: Research and write the report (report.md) comparing Ollama, llama.cpp, vLLM, and LM Studio based on the design.md. For each of the 5 viewpoints, provide detailed analysis with source URLs. Conclude with a clear judgment on Ollama's suitability as the base for 'mu' based on the definition of 'suitable' (minimized management effort and stable API/tool integration).
   - 成功条件: report.md must contain a comparison of the 4 tools across the 5 defined viewpoints, include source URLs, and provide a final judgment regarding Ollama.
   - 検査: `powershell -ExecutionPolicy Bypass -File verifier.ps1` → 「PASS」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Independently verify that the report.md fulfills all requirements of the SPEC: 4 tools compared, 5 viewpoints addressed, evidence URLs provided, and a definitive judgment on Ollama's continued use for 'mu' based on the provided definitions.
   - 成功条件: The verdict.md must state 'PASS' if the report meets all SPEC criteria, otherwise 'FAIL' with reasons. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
