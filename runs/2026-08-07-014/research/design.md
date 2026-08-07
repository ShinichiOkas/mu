# Design Document: Evaluation Report for LLM Runtime (report.md)

This document defines the structure and design rules for `report.md`, which evaluates LLM runtimes to determine the optimal choice for the 'mu' project.

## 1. Structure of report.md

The report shall follow this hierarchical structure:

### 1.1 Executive Summary
- **Conclusion**: A clear statement on whether to continue using Ollama or migrate to another tool.
- **Decision Logic**: The reasoning behind the conclusion based on the weighted evaluation of the 5 criteria.

### 1.2 Comparison Matrix
A Markdown table comparing the target tools across the defined evaluation criteria.

| Criterion | Ollama | llama.cpp | vLLM | LM Studio |
| :--- | :---: | :---: | :---: | :---: |
| Resource usage | | | | |
| Setup ease | | | | |
| API compatibility | | | | |
| Inference speed | | | | |
| Model flexibility | | | | |

### 1.3 Detailed Evaluation (The 5 Viewpoints)
For each criterion, provide a qualitative and quantitative analysis:

1. **Resource usage**: Memory footprint (VRAM/RAM), CPU/GPU overhead during idle and peak load.
2. **Setup ease**: Installation complexity, dependency management, time to "first token".
3. **API compatibility**: Adherence to OpenAI API standards, ease of integration with existing 'mu' components.
4. **Inference speed**: Tokens per second (TPS), latency for first token, throughput under concurrent requests.
5. **Model flexibility**: Support for various formats (GGUF, EXL2, AWQ, etc.), ease of adding custom models.

### 1.4 Decision Logic for 'mu'
A dedicated section explaining the specific needs of the 'mu' project and how the tools map to these needs.
- **Requirement A** $\rightarrow$ **Tool X** provides this.
- **Trade-off analysis**: Why a specific weakness in the chosen tool is acceptable (or why a strength in another is irrelevant).

---

## 2. Quality Attributes and Realization

### 2.1 Verifiability
To ensure the report is based on actual evidence and not conjecture, the following structure is mandated:
- **Evidence Markers**: Every claim in the "Detailed Evaluation" section must be accompanied by a reference to a test result or a specific version number (e.g., `[Test: GPU_MEM_01]`).
- **Comparison Consistency**: The same hardware and model (e.g., Llama-3-8B) must be used for all 4 tools to ensure a fair comparison.

### 2.2 Objectivity
The decision logic must be decoupled from the evaluation criteria. The criteria provide the data; the logic provides the interpretation based on 'mu's specific constraints.

---

## 3. Design Rules

The implementation of `report.md` must adhere to the following rules:

- **Read-Only Inputs**: Any benchmark logs or specification files used as input must be treated as read-only.
- **Artifact Limitation**: Only `report.md` shall be created as the final output. Temporary calculation sheets or raw logs must be deleted or stored in a dedicated `/tmp` directory (not committed).
- **Naming Conventions**: Use the exact strings for criteria:
    - `Resource usage`
    - `Setup ease`
    - `API compatibility`
    - `Inference speed`
    - `Model flexibility`
- **Tool Scope**: Only the following 4 tools are to be evaluated: `Ollama`, `llama.cpp`, `vLLM`, and `LM Studio`.
