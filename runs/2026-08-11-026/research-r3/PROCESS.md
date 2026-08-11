# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [ ] **researcher** → `research_notes.md`
   - task: Research the four LLM execution frameworks (Ollama, llama.cpp, vLLM, LM Studio) focusing on the four key perspectives: deployment cost, resource efficiency, extensibility, and operational stability. Collect technical specifications and official documentation URLs for every claim made.
   - 成功条件: Detailed notes for all 4 tools across all 4 perspectives, each single claim accompanied by a source URL.
   - 検査: `Get-ChildItem research_notes.md` → 「research_notes.md」
2. [ ] **researcher** → `report.md`
   - task: Synthesize the research into a final report (`report.md`). The report must include a comparison table/section covering the 4 tools and 4 perspectives, include source URLs for all factual claims, and provide a clear conclusion on whether Ollama should continue to be used as the foundation for 'mu' based on the defined criteria for appropriateness.
   - 成功条件: The report contains Ollama, llama.cpp, vLLM, LM Studio, and the 4 perspective terms (導入コスト, リソース効率, 拡張性, 運用安定性), a section marked '結論', and source URLs for all claims.
   - 検査: `Get-Content report.md` → 「Ollama」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that `report.md` fulfills all SPEC requirements: presence of the 4 tools, the 4 comparison axes, a conclusion regarding Ollama, and critically, verify that every claim in the report is backed by a source URL. Use the 'judge' tool to ensure the quality of the arguments and the grounding of claims.
   - 成功条件: All mechanical checks pass and manual verification of source URL grounding is successful. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Test-Path verdict.md` → 「True」
