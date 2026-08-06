# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design the structure of the comparison report. Define the comparison table layout covering the 4 perspectives (Low resource, API compatibility, Setup ease, Update frequency) and the logical flow from analysis to the conclusion for 'mu'.
   - 成功条件: The design must explicitly map how the 4 perspectives will be evaluated and how the conclusion for Ollama will be derived.
2. [ ] **implementer** → `verify_report.ps1`
   - task: Build a PowerShell verification script that checks if 'comparison_report.md' contains all four target bases (Ollama, llama.cpp, vLLM, LM Studio), contains 'http' links, and contains the word '結論'.
   - 成功条件: The script should print 'PASS' if all criteria are met, and 'FAIL' otherwise.
3. [ ] **implementer** → `comparison_report.md`
   - task: Research and create the 'comparison_report.md'. Include the comparison table based on the 4 perspectives, provide URL sources for each claim, and conclude whether to continue using Ollama for the 'mu' project based on minimalism.
   - 成功条件: The report must fulfill all requirements in the SPEC and pass the verification script.
   - 検査: `powershell -ExecutionPolicy Bypass -File verify_report.ps1` → 「PASS」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Perform a final review of 'comparison_report.md' against the SPEC. Verify the accuracy of the comparison, the validity of the URLs, and the clarity of the conclusion regarding Ollama.
   - 成功条件: Verdict must be 'PASS' only if the report is comprehensive, cited, and provides a clear decision for mu. / 判定書が ACHIEVED（yes|no|uncertain）・REASON・GAP の3項目を含む
