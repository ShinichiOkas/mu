# Design Document: LLM Runtime Comparison Report

## 1. Structure

### File Configuration
- **Output File**: `comparison_report.md` (Markdown format)

### Logical Flow
The report shall follow this sequence to ensure a logical progression from data to decision:
1. **Introduction**: Brief statement of the purpose (evaluating LLM runtimes for the "mu" minimal agent).
2. **Comparison Matrix**: A high-level summary table for quick reference.
3. **Detailed Analysis**: In-depth evaluation of the critical factors for a minimal agent.
4. **Conclusion**: Final recommendation regarding Ollama's suitability.
5. **Evidence/References**: Listing of all sources used.

### Comparison Table Columns
The comparison table must include the following columns for each runtime (Ollama, llama.cpp, vLLM, LM Studio):
- **Setup Difficulty**: Ease of installation and initial configuration.
- **Resource Consumption**: Memory footprint, CPU/GPU utilization.
- **API Compatibility**: Support for OpenAI API or other standard interfaces.
- **Model Formats**: Supported formats (e.g., GGUF, AWQ, GPTQ).
- **Throughput**: Inference speed/performance.
- **Primary Use Case**: Intended primary target audience or scenario.

### Analysis Flow for Minimal Agents
The detailed analysis must specifically address the "mu" agent's requirements:
- **Low Overhead**: Prioritize tools that do not bloat system resources.
- **Rapid Deployment**: Favor tools with minimal setup scripts or binary installations.
- **Extensibility**: Evaluate the ease of integrating the API into a minimal Python/TypeScript environment.
- **Trade-off Analysis**: Compare if the performance gain of high-throughput tools (like vLLM) justifies the increased resource/setup cost for a "minimal" agent.

### Conclusion Section
The conclusion must explicitly answer: **"Should Ollama be continued as the base for mu?"**
- **Verdict**: Clear Yes / No / Conditional Yes.
- **Reasoning**: Derived directly from the comparison table and analysis (e.g., "Ollama wins on setup difficulty and API compatibility, which outweighs vLLM's throughput for a minimal agent").

### Placement of Evidence
- **In-line Citations**: Every specific claim (e.g., "vLLM supports PagedAttention") must be followed by a URL in brackets `[URL]`.
- **Reference List**: A consolidated list of all URLs at the end of the document.

## 2. Quality Attributes and Realization

### Verifiability
To ensure the report is not a hallucination and meets specifications:
- **Keyword Presence**: The implementer must ensure keywords "リソース消費量" (Resource Consumption) and "セットアップ" (Setup) are used.
- **Link Validation**: All provided URLs must be functional and lead to official documentation or reputable benchmarks.
- **Completeness Check**: A checklist should be used by the implementer to verify all 4 tools and all 6 table columns are present.

## 3. Design Rules

### Implementation Constraints
- **Input Files**: Any input files provided are **read-only**. Do not modify `SPEC.md` or `PROCESS.md`.
- **Artifacts**: Create **only** the `comparison_report.md` file. Do not leave temporary search logs or scrapings in the working directory.
- **Language**: The report should be written in Japanese (as per SPEC.md requirements for keywords), but technical terms may remain in English.

### Formatting Rules
- **Table**: Use standard Markdown table syntax.
- **Conclusion**: The conclusion must be a distinct section with a clear header `## 結論`.
- **Evidence**: URLs must be full links starting with `http://` or `https://`.
