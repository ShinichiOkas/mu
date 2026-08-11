# Research Notes: LLM Deployment Tools

## Ollama
- **Deployment Cost**: Primarily focused on local deployment, reducing cloud API costs. It is free and open-source for local use.
  - Source: https://ollama.com/
- **Resource Efficiency**: Designed for local efficiency, supporting various hardware including AMD GPUs (via ROCm) and Apple Silicon.
  - Source: https://docs.ollama.com/linux
- **Extensibility**: Provides a REST API and official libraries for Python and JavaScript, allowing it to be integrated into other applications. It uses a "Modelfile" to define model configurations.
  - Source: https://docs.ollama.com/index
- **Operational Stability**: Supports Docker deployment for consistent environments across different platforms.
  - Source: https://deepwiki.com/ollama/ollama/6.3-docker-deployment

## llama.cpp
- **Deployment Cost**: Minimal setup cost. It is a plain C/C++ implementation without dependencies, making it highly portable for local and cloud deployment.
  - Source: https://github.com/ggml-org/llama.cpp
- **Resource Efficiency**: Extremely efficient through GGUF quantization (1.5-bit to 8-bit), supporting CPU+GPU hybrid inference to run models larger than VRAM.
  - Source: https://github.com/ggml-org/llama.cpp/blob/master/README.md
- **Extensibility**: Highly extensible with support for numerous backends (CUDA, Metal, HIP, Vulkan, SYCL, etc.) and a built-in HTTP server for OpenAI-compatible API access.
  - Source: https://github.com/ggml-org/llama.cpp/blob/master/README.md
- **Operational Stability**: Robust performance across a wide range of hardware, including Apple Silicon, x86 (AVX/AMX), and RISC-V.
  - Source: https://github.com/ggml-org/llama.cpp/blob/master/README.md

## vLLM
- **Deployment Cost**: Focused on "cheap LLM serving for everyone" by maximizing throughput, which reduces the cost per request in production environments.
  - Source: https://vllm.ai/
- **Resource Efficiency**: High memory efficiency via **PagedAttention**, which eliminates fragmentation in the KV cache, and continuous batching for high throughput.
  - Source: https://docs.vllm.ai/en/latest/design/paged_attention/
- **Extensibility**: Seamless integration with Hugging Face and support for various quantization schemes (GPTQ, AWQ, FP8). It is designed as a library for high-performance serving.
  - Source: https://vllm.ai/
- **Operational Stability**: Engineered for production scale with features like CUDA/HIP graphs and support for distributed deployments.
  - Source: https://docs.vllm.ai/en/latest/

## LM Studio
- **Deployment Cost**: Local-first platform that eliminates cloud costs for users running models on their own hardware.
  - Source: https://lmstudio.ai/docs
- **Resource Efficiency**: Provides a GUI for configuration and utilizes optimization techniques to improve response time and memory efficiency.
  - Source: https://deepwiki.com/lmstudio-ai/docs/7-advanced-features
- **Extensibility**: Offers a developer-centric approach with TypeScript and Python SDKs, a CLI tool (`lms`), and OpenAI/Anthropic-compatible REST API endpoints.
  - Source: https://lmstudio.ai/docs/developer
- **Operational Stability**: Supports "headless" deployments via `llmster`, allowing the core engine to run as a daemon on servers or cloud instances without the GUI.
  - Source: https://lmstudio.ai/docs/developer
