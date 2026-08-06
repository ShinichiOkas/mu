# 判定書 - comparison_report.md vs SPEC

## 検証対象
比較報告書：`comparison_report.md`  
仕様定義：`SPEC.md`(read-only)  

## ACHIEVED: no (不合格) の理由

### 1. SPEC 目的（PURPOSE）原文の制約との整合性確認 - OK ✅
```spec_original_purpose_lines_from_SPEC PURPOSE section:
"ローカルで LLM を動かす実行基盤について、Ollama / llama.cpp / vLLM / LM Studio を比較し、mu の基盤として Ollama を使い続けるべきかを判断できる材料を、報告書にまとめてほしい。...主張には必ず出典 URL を添えること"
```

SPEC は目的の原文を弱体化していない：4 つすべて（Ollama, llama.cpp, vLLM, LM Studio）を比較し、各ツールへの出典 URL が必要 → SPEC の制約が守られているのは OK。問題は実装側の不完全さである。

### 2. 受入基準 (Acceptance Criteria) 検査結果 - ❌ FAIL

| # | Acceptance Criterion | Expected by Specification | Actual State in comparison_report.md | Result |
|---|----------------------|---------------------------|--------------------------------------|--------|
| AC1 | ファイル存在 (`Test-Path` → True) | File must exist at `comparison_report.md` path | Exists ✅ | **PASS** |
| AC2 | 4 つの基盤すべて記載 (Ollama, llama.cpp, vLLM, LM Studio) | All four tools: Ollama ✓ / llama.cpp ✓ / vLLM ✗✘/LMStudio✗❅→ appears only as pass-through text in section header once each without dedicated analysis sections requiring URLs ⚠️⭕ (only 2 of 4 have proper analysis with claims needing URL support) ❌FAIL | **FAIL** – VLLM & LM Studio について、SPEC が要求する「比較表形式」「各ツールの性能や機能に関する主張への出典URL」セクションが存在しない。Ollama/llama.cpp のみが分析対象として扱われているのみで、VLLM/LM Studio は名称のみの言及 | ❌ FAIL |
| AC3 | 主張に対する出典 URL 添付 (`Select-String 'http'` → http を含む) | Claims on tool performance/features must have valid source URLs from official docs/GitHub/trusted blogs | Ollama: https://docs.ollama.com/* links ✅ / llama.cpp: implicit in table & text but no dedicated section with URL required ❅? VLLM/LM Studio: No analysis sections exist so claims needing URLs are absent ⚠️⭕ → SPEC 要件は「各ツールの性能や機能に関する主張」に URL を添えること、VLLM と LM Studio のセクションが存在しないため「すべてのツールについて根拠が提示されている」という要件を満たさない ❌ FAIL | **FAIL** (vLLM, LM Studio lack sections with claims+URLs) 検証コマンドで `http` が 5 URL 検出される（Sources セクションのみ）だが、ツールの主張に紐付いた URL は不足 ⚠️⭕SPEC の「各ツールへの URL」要件は不十分 | ❌ FAIL on FULL COVERAGE for ALL FOUR TOOLS (2/4 OK, 2 missing) |
| AC4 | Ollama 継続利用可否の結論明記 (`Select-String '結論'` → 「結論」と含む) | Clear decision: continue or switch away from using Ollama as mu base | Section "## 3. 結論 (Final Conclusion)" exists with statement："mu is preferred for use cases requiring extreme minimalism... **continue using Ollama**" ✅ | **PASS** |

→ Overall AC status: ❌ FAIL due to #2, #3 not fully satisfied  

### 3. Success Condition Verification - ⚠️ NOT MET / ACHIEVED=no
検証コマンドが期待する出力条件：`>4` matches for `local.*LLM|Ollama|llama.cpp|vLLM|LM Studio`  
現在の結果：

```powershell
(Get-Content comparison_report.md -Raw | Select-String "local.*LLM|Ollama") → Count = 1 ("Local LLM Runtime Comparison" URL title mentions local/LLMs) OR matches: only Ollamy appears in the entire doc. The regex `local.L*L` may match differently than specified (the success condition says ensure coverage for ALL FOUR tools AND valid URLs per tool, which is not achieved → count below threshold even though "Ollama" keyword many times alone doesn't reach ≥4 without proper matches
Also, verification command: Get-Content ... | Select-String "local.*LLM|Ollama..." returns 1 match only (from phrase containing local or Ollamy in one section), not the expected >4. The success condition explicitly ensures coverage of all four tools AND valid URLs on claims → which is FAILED because VLLM/LM Studio lack analysis sections with sources
```

→ Success Condition: **NOT MET** due to insufficient match count (< 4) and missing tool coverage for vLLM & LM Studio  

### 4. SPEC Weakness Check - ✅ No Constraint Weakening Detected  
SPEC が目的の原文から制約を弱めていないことを確認：「すべて記載」「URL を添える」はそのまま仕様化されている → これは OK。不合格理由は実装側（comparison_report.md）の不備であり、仕様が緩和されたわけではない  

### 5. Design Rules Violation Check - ✅ No Extra File Modifications  
- SPEC で定義した納品物 `comparison_report.md` のみ対象で、入力ファイルの記述に不具合ありは仕様変更とはならない → DESIGN RULES OK（ただし実装欠陥）

### 6. Source URL Validity for Each Tool (SPEC Requirement) - ❌ INCOMPLETE  
| Tool | Analysis Section Exists? | Claims Needing URLs in Spec | Valid Source URL Provided per SPEC requirement? | Status |
|------|--------------------------|----------------------------|--------------------------------------------------|--------|
| Ollama  | Yes (multiple sections covering setup, API compat, resource usage) | **Yes** – "Ollama excels in Setup ease and Update frequency... bridge to API compatibility..." etc → URLs: https://docs.ollama.com/gpu /api/openai-compatibility ✅ | YES ✅
| llama.cpp  | Partial (mentioned as Ollama's dependency, not analyzed separately) | Spec lists it as comparison target but no dedicated section with claims needing URL support ⚠️⭕ | PARTIAL/MISSING – No separate analysis requiring source link exists for its own performance/features | ❌FAIL on STANDALONE COVERAGE
| vLLM    | NO (only mentioned once in "When compared to high-throughput engines like VLLM or GUI-based tools..." → pass-through mention, not analyzed)  | Spec requires comparison across all four with source URLs per claim; no analysis section for VLLM exists ⚠️❅✗ ❌FAIL
| LM Studio   | NO (only mentioned once as "GUI-based tools like LM Studio" in same sentence – name drop only without dedicated claims or URL-backed evaluation)  | No analysis, therefore zero claims needing URLs → however SPEC requires all four to be compared and have source URLs for their performance/feature claims; absence of section = non-compliance ❌FAIL

→ Only Ollama has proper coverage with valid sources ✅. The other three fail on full compliance because VLLM/LM Studio sections are missing entirely, llama.cpp only appears as dependency reference without standalone evaluation per tool in the comparison table format required by SPEC。SPEC の「4 つのツールすべてを基盤として記載（比較表形式）」→ 要件は満たされているが、「各ツールの性能や機能に関する主張には必ず公式サイトの...出典 URL を併記」について llama.cpp は依存関係での言及のみ、VLLM/LMS studio は分析セクションなしで「URL の添付が必要な主張が存在しない」という状態だが、SPEC が要求する「4 つすべてが比較対象として適切に扱われること」（各ツールごとに性能/機能評価+出典）は不十分

## 結論・判定書まとめ
**ACHIEVED: no（不合格）**  

主たる問題点：  
1. SPEC の受入基準 AC2 (AC3) に反する → vLLM と LM Studio は「分析セクション」としての主張に URL を添えるべきだが、これらが存在せず、実装が仕様を完全に満たしていない  
2. Success Condition (`>4` matches in verification command output) 不備あり。現状 `local.*LL*M|Ollama` のマッチ数は期待値（≥4）を満たさない  

SPEC は目的の原文から制約を引き落たものでない →不合格の原因は実装側のみであり、修正対象が比較報告書 (`comparison_report.md`) にあるべき  

## 対応方針 (Spec Compliance Path)
- `comparison_report.md` を再作成または編集し：  
  - Ollama/llama.cpp/vLLM/LM Studio の各々について独立した分析セクションを追加（既存の表形式で OK）  
  - VLLM, LM Studio の性能・機能に関する主張に、公式ドキュメント/GitHub リポジトリ等の信頼できる出典 URL を追加する必要あり → 「すべてのツール」について「URL で裏付けられた主張」が必要  

SPEC は目的（ローカル LLM 実行基盤の比較と Ollama 継続利用判定＋4 つすべて+各ツールの URL）を引き継いでおり弱体化していないため、不合格は実装側の不完全さゆえであり、comparison_report.md を修正する必要がある
