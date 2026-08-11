# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu（きわめてミニマルな汎用エージェント）の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。判断に効く観点で比べ、主張には必ず出典 URL を添えること。

## タスク列
1. [ ] **researcher** → `comparison_report.md`
   - task: Research and compare the LLM execution frameworks (Ollama, llama.cpp, vLLM, LM Studio) based on resource consumption, setup cost, and API versatility. For every claim regarding performance or features, find and record the official documentation or GitHub repository URL. Evaluate whether Ollama remains the most appropriate base for 'mu' based on its minimalist philosophy.
   - 成功条件: The report must include all 4 tools, all 3 comparison axes, a clear conclusion on whether to stick with Ollama, and a supporting URL for every technical claim.
   - 検査: `Get-Content "comparison_report.md"` → 「Ollama」
2. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the comparison_report.md fulfills all SPEC requirements: presence of the 4 tools, the 3 specified comparison axes, a clear conclusion, and valid source URLs for all claims. Use the judge tool to confirm if the conclusion is logically sound based on the presented evidence.
   - 成功条件: The report passes if all 4 tools are listed, the 3 axes are discussed, the conclusion is explicit, and all claims are grounded in provided URLs. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Test-Path "verdict.md"` → 「True」
