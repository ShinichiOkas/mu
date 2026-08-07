# LLM Runtime Evaluation Report

## 1.1 Executive Summary
- **Conclusion**: Continue using **Ollama (Tool1)**.
- **Decision Logic (判断)**: For the 'mu' project's current stage (prototyping and developer-centric internal tools), Ollama (Tool1) provides the optimal balance of setup ease, API compatibility (View3), and resource efficiency. While vLLM (Tool3) offers superior concurrent throughput, it introduces significant deployment complexity (Linux/WSL2 requirement, Python/CUDA dependencies) and is overkill for a single-user or small-team environment. Ollama (Tool1)'s recent integration of MLX for Apple Silicon and its seamless OpenAI-compatible API make it the most pragmatic choice.

## 1.2 Comparison Matrix

| Criterion | Ollama (Tool1) | llama.cpp (Tool2) | vLLM (Tool3) | LM Studio (Tool4) |
| :--- | :---: | :---: | :---: | :---: |
| Resource usage (View1) | Low/Medium | Lowest | High (VRAM optimized) | Medium (Electron overhead) |
| Setup ease (View2) | Excellent | Medium | Complex | Excellent |
| API compatibility (View3) | Excellent | Good | Excellent | Good |
| Inference speed (View4) | Medium | Medium | Highest (Concurrent) | Medium/High |
| Model flexibility (View5) | Good | Highest | High (HF native) | Good |

## 1.3 Detailed Evaluation (The 5 Viewpoints)

### 1. Resource usage (View1)
- **Ollama (Tool1)**: Low to medium footprint. Wraps llama.cpp (Tool2)/MLX. Memory efficiency is moderate, with some overhead from the Go wrapper [Source: codersera.com].
- **llama.cpp (Tool2)**: Lowest footprint. Direct C++ implementation with minimal overhead. Ideal for edge/embedded devices [Source: codersera.com].
- **vLLM (Tool3)**: High overall resource demand but extremely efficient VRAM usage via PagedAttention (wasting <4% of VRAM compared to 30-50% in others) [Source: codersera.com].
- **LM Studio (Tool4)**: Medium footprint. Adds 300-500 MB RSS overhead due to the Electron-based GUI shell [Source: codersera.com].

### 2. Setup ease (View2)
- **Ollama (Tool1)**: Excellent. One-line installation and Docker-style model management (`ollama pull`) [Source: codersera.com].
- **llama.cpp (Tool2)**: Medium. Requires compilation or binary management; manual GGUF handling [Source: codersera.com].
- **vLLM (Tool3)**: Complex. Requires Linux/WSL2, specific CUDA/ROCm versions, and Python environment management [Source: codersera.com].
- **LM Studio (Tool4)**: Excellent. GUI-driven installation and model discovery via integrated Hugging Face browser [Source: codersera.com].

### 3. API compatibility (View3)
- **Ollama (Tool1)**: Excellent. Provides a native OpenAI-compatible REST API at `:11434`, widely supported by agentic frameworks (Cursor, Continue) [Source: codersera.com].
- **llama.cpp (Tool2)**: Good. Offers a server mode (`llama-server`), though less "plug-and-play" than Ollama (Tool1) [Source: codersera.com].
- **vLLM (Tool3)**: Excellent. Built for production API serving with high adherence to OpenAI standards and support for complex serving patterns [Source: codersera.com].
- **LM Studio (Tool4)**: Good. Provides a local server mode, though primarily targeted at GUI users [Source: codersera.com].

### 4. Inference speed (View4)
- **Ollama (Tool1)**: Medium. Single-user performance is comparable to llama.cpp (Tool2), but throughput collapses under concurrent load (~40 tok/s peak) [Source: codersera.com].
- **llama.cpp (Tool2)**: Medium. High efficiency for single-user; serves as the engine for Ollama (Tool1) [Source: codersera.com].
- **vLLM (Tool3)**: Highest. Optimized for concurrent throughput using continuous batching and PagedAttention, hitting 16-20x the throughput of Ollama (Tool1) under load [Source: codersera.com].
- **LM Studio (Tool4)**: Medium/High. Competes well on Mac via MLX and offers continuous batching in newer versions [Source: codersera.com].

### 5. Model flexibility (View5)
- **Ollama (Tool1)**: Good. Curated library of ~150 models; supports GGUF imports [Source: codersera.com].
- **llama.cpp (Tool2)**: Highest. Native GGUF support; widest range of architectures and quantization controls (1.5-bit to 8-bit) [Source: codersera.com].
- **vLLM (Tool3)**: High. Best support for Hugging Face safetensors, AWQ, GPTQ, and FP8 [Source: codersera.com].
- **LM Studio (Tool4)**: Good. Direct access to any GGUF/MLX model on Hugging Face via GUI [Source: codersera.com].

## 1.4 Decision Logic (判断) for 'mu'
- **Rapid Prototyping** $\rightarrow$ **Ollama (Tool1)**'s one-command setup and model management minimize "time to first token".
- **Integration Effort** $\rightarrow$ **Ollama (Tool1)**'s OpenAI-compatible API allows 'mu' to swap models or move to a production server (like vLLM (Tool3)) in the future with minimal code changes.
- **Hardware Versatility** $\rightarrow$ Ollama (Tool1)'s 2026 update (v0.19+) incorporating MLX ensures high performance on Apple Silicon while maintaining x86 compatibility via llama.cpp (Tool2).
- **Trade-off Analysis**: The lack of high concurrent throughput in Ollama (Tool1) is acceptable because 'mu' is currently a developer-focused tool with low concurrency requirements. The complexity of vLLM (Tool3) (Linux/CUDA requirement) is an unnecessary burden at this stage.

**Sources**:
- https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/
