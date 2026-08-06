# Design Document: LLM Comparison Report

## 1. Structure
The report will be structured as a comparison between 'mu' and 'Ollama', focusing on four specific perspectives to derive a final conclusion.

### 1.1 Comparison Table Layout
The comparison will be presented in a table format with the following columns:
- **Perspective**: The criteria being evaluated.
- **mu**: Evaluation and score/status for mu.
- **Ollama**: Evaluation and score/status for Ollama.
- **Verdict**: Comparison result for that specific perspective.

#### Perspectives Definition:
1. **Low resource**: Ability to run on hardware with limited VRAM/RAM. Evaluation of quantization support and memory footprint.
2. **API compatibility**: Adherence to industry standards (e.g., OpenAI API spec) to ensure ease of integration with existing tools.
3. **Setup ease**: Time and complexity required from installation to first successful inference.
4. **Update frequency**: Recency of updates and speed of supporting new model architectures.

### 1.2 Logical Flow for 'mu'
The analysis for 'mu' will follow this logical sequence:
1. **Feature Analysis**: Identify the core architectural strengths of 'mu' regarding the 4 perspectives.
2. **Comparative Mapping**: Map 'mu's capabilities against the benchmarks set by Ollama.
3. **Gap Analysis**: Identify where 'mu' excels or falls short.
4. **Synthesis**: Aggregate the findings from the 4 perspectives to form a cohesive conclusion on 'mu's value proposition.
5. **Final Conclusion**: A definitive statement on the primary use case where 'mu' is the superior choice.

---

## 2. Quality Characteristics and Verification
To ensure the report is based on factual analysis rather than guesswork, the following verification structure is required:

- **Traceability**: Each claim in the comparison table must be traceable to a specific feature or documentation point.
- **Verification Marker**: The implementation script (if any) used to gather data must output a summary of its execution:
  - Format: `[TEST_COUNT: X][SUCCESS: Y][FAILURE: Z]`
  - This prevents "silent failures" where a script exits with code 0 but performs no actual analysis.

---

## 3. Design Rules
The following rules must be strictly followed during the implementation phase:

### 3.1 File Handling
- **Input files are read-only**: Any input specification or data files provided must not be overwritten, edited, or deleted.
- **Output constraint**: Create only the files explicitly named in the specification. Do not leave temporary files, logs, or scratchpads in the working directory.

### 3.2 Content Rules
- **Consistency**: Use the exact terms "Low resource", "API compatibility", "Setup ease", and "Update frequency".
- **Objective Tone**: Use evidence-based language (e.g., "Supports X" instead of "is great at X").
- **Mapping Clarity**: The mapping from Ollama's evaluation to the final conclusion must be explicit (e.g., "Since Ollama excels in X but mu excels in Y, mu is preferred for Z").
