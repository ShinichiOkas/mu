# Local LLM Runtime Comparison Report

## 1. Overview
This report compares four prominent tools for running Large Language Models (LLMs) locally: **Ollama**, **llama.cpp**, **vLLM**, and **LM Studio**. The goal is to determine the most suitable runtime based on resource consumption, setup complexity, and specific needs.

## 2. Detailed Comparison

| Feature | Ollama | llama.cpp | vLLM | LM Studio |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Role** | Experience Layer (CLI/API) | Inference Engine (C++) | Serving System (Production) | Experience Layer (GUI) |
| **Setup Complexity** | Very Low (One-line install) | Moderate (Build from source/Binary) | High (Python/CUDA env) | Very Low (Installer) |
| **Resource Consumption** | Low to Moderate (Wraps llama.cpp) | Very Low (Highly optimized C++) | High (Optimized for GPU VRAM) | Moderate (GUI overhead) |
| **Throughput** | Single-user optimized | High (Single-user/Edge) | Ultra High (Concurrent/Batch) | Moderate to High |
| **Target Hardware** | macOS, Linux, Windows | Almost any (CPU, GPU, Edge) | NVIDIA/AMD GPUs (Linux/WSL2) | macOS, Windows |
| **Model Format** | GGUF, MLX | GGUF | Safetensors, AWQ, GPTQ, FP8 | GGUF, MLX |
| **Best Use Case** | Developer prototyping, Agents | Embedded, Edge, Custom HW | Production API, Multi-user | Model browsing, Non-CLI users |

### 2.1 Resource Consumption (リソース消費量)
- **llama.cpp** is the baseline for efficiency, designed to run on everything from high-end GPUs to basic CPUs with minimal overhead.
- **Ollama** and **LM Studio** wrap engines like llama.cpp (and MLX for Mac), meaning their resource consumption is similar to the engine plus a small management layer.
- **vLLM** is designed for maximum throughput using PagedAttention. It consumes significantly more VRAM to manage KV caches for concurrent users, making it unsuitable for low-resource local machines but ideal for server-grade GPUs.

### 2.2 Setup Complexity (セットアップ)
- **Ollama** and **LM Studio** offer the easiest setup. Ollama provides a simple CLI and REST API, while LM Studio provides a full GUI for discovering and downloading models from Hugging Face.
- **llama.cpp** requires more manual effort, often involving compilation or managing specific binaries to match the hardware.
- **vLLM** has the steepest learning curve, requiring a specific Python environment and typically a Linux-based OS (or WSL2) with configured CUDA drivers.

## 3. Synthesis for mu's Needs
Depending on the specific phase of development:
- **For rapid prototyping and agent integration:** Ollama is the strongest candidate due to its OpenAI-compatible API and near-zero setup time.
- **For deployment on constrained hardware:** llama.cpp provides the finest control over memory and quantization.
- **For scaling to multiple concurrent users:** vLLM is the only viable option among these four.

## 4. Conclusion
**Should we continue with Ollama?**
**Yes.** For local development and prototyping, Ollama provides the best balance of setup ease and performance. Since it wraps llama.cpp, it leverages the efficiency of GGUF models while providing a modern API that integrates easily with other tools. Unless there is a strict requirement for multi-user concurrent serving (vLLM) or extreme hardware optimization (llama.cpp), Ollama remains the most productive choice.

## 5. Sources
- Codersera: [Ollama vs LM Studio vs vLLM vs llama.cpp vs MLX 2026](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
