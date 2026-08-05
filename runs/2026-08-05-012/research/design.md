# Design Document: LLM Tool Comparison Report

## 1. Purpose
The goal of this report is to determine the optimal LLM inference engine for "mu", a minimal agent. The selection is based on minimizing overhead while maximizing accessibility and efficiency.

## 2. Structure
The report will be structured as follows:
- **Executive Summary**: Final recommendation and the core reason based on mu's nature.
- **Evaluation Matrix**: A comparative table of the 4 tools across 4 perspectives.
- **Detailed Analysis**: Qualitative and quantitative reasoning for each perspective.
- **Conclusion Logic**: The derivation process used to arrive at the final recommendation.

### File Composition
- `report.md`: The final comparison report containing the above sections.

## 3. Evaluation Criteria & Metrics
Each tool (Ollama, llama.cpp, vLLM, LM Studio) will be evaluated based on the following metrics:

| Perspective | Metric | Evaluation Focus |
| :--- | :--- | :--- |
| **Setup** | Time-to-First-Token (TFFT) Setup | Ease of installation, dependency complexity, and time required to start the first inference. |
| **API** | Compatibility & Overhead | OpenAI API compatibility, ease of integration with minimal agents, and REST overhead. |
| **Resource** | Footprint (RAM/VRAM) | Idle memory usage, peak memory during inference, and efficiency of quantization support. |
| **Cost** | Operational Cost | Total Cost of Ownership (TCO) including hardware requirements and time spent on maintenance. |

## 4. Conclusion Derivation Logic
The final recommendation will be derived using a "Minimalism Weighting" logic:

1. **Weighting**: Because "mu" is a *minimal agent*, the weights are assigned as follows:
   - Setup (20%): Low weight; one-time cost.
   - API (30%): High weight; critical for the agent's seamless communication.
   - Resource (40%): Highest weight; minimal agents must be lightweight to avoid resource starvation of the host system.
   - Cost (10%): Low weight; focused on efficiency.

2. **Scoring**: Each tool is scored 1-5 for each metric.
3. **Decision Rule**:
   - The tool with the highest weighted score is the primary recommendation.
   - If two tools are close, the one with the lowest **Resource Footprint** wins (Minimalist Tie-breaker).

## 5. Quality Characteristics & Verification
To ensure the report is verifiable and objective:
- **Data Evidence**: Every score in the matrix must be backed by a specific observation (e.g., "Ollama: 5/5 for Setup due to single-command install").
- **Verification Marker**: The final report must include a summary table that lists all 4 tools (Ollama, llama.cpp, vLLM, LM Studio) to ensure no tool was omitted.

## 6. Design Rules
- **Read-Only Input**: Any existing specification files are read-only.
- **Output Limitation**: Only `report.md` (and this `design.md`) shall be produced. No temporary log files or scrap folders.
- **Marker Requirement**: The final report must explicitly contain the names "Ollama", "llama.cpp", "vLLM", and "LM Studio" in the Evaluation Matrix.
- **Comparison Logic**: Use a quantitative table followed by qualitative justification.
