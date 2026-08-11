# ローカルLLMランタイム比較報告書

本報告書では、ローカル環境でLLMを動作させるための主要な4つのツール（Ollama, llama.cpp, vLLM, LM Studio）について、指定の基準に基づき比較検証した結果をまとめる。

## セットアップの容易さ
- **Ollama**: 極めて容易。ワンラインのインストールが可能で、Dockerのようなコマンド（`ollama pull`）でモデルの取得から実行まで完結する。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **LM Studio**: 容易。GUIベースのアプリケーションであり、Hugging Faceからのモデル検索・ダウンロードがアプリ内で完結するため、CLI操作を必要としない。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **vLLM**: 中程度。Pythonベースのサーバーであり、主にLinux環境（NVIDIA/AMD GPU）を想定している。WindowsではWSL2が必要となる。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **llama.cpp**: 低〜中程度。C/C++バイナリであり、環境に合わせたコンパイルやビルドが必要な場合がある。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]

## API互換性
- **Ollama**: 高い。`localhost:11434` で OpenAI 互換の REST API を提供しており、多くのエージェントフレームワーク（Cursor, Continue等）が標準的に対応している。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **vLLM**: 高い。プロダクション向けのサービングシステムとして設計されており、高い互換性とスループットを持つ。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **LM Studio**: 提供。ヘッドレスモードでのサーバー起動により、API経由の利用が可能。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **llama.cpp**: 提供。シンプルなサーバー機能を持ち、Ollamaなどの上位レイヤーの基盤となっている。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]

## リソース消費量
- **llama.cpp**: 非常に効率的。CPUのみの環境や、エッジデバイスなどの制限されたハードウェアでも動作するように設計されている。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **Ollama**: 効率的。内部でllama.cppやMLX（Apple Silicon向け）を利用しており、一般的に低リソースで動作する。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **LM Studio**: 効率的。GGUF形式を利用しており、ユーザーのRAM/GPU容量に応じた量子化モデルの推奨機能を持つ。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **vLLM**: 高い。PagedAttentionなどの機能により効率化されているが、基本的にはデータセンター級のGPU（A100, H100等）での運用を前提としている。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]

## モデル導入の手間
- **Ollama**: 最小。`ollama pull` コマンド一つで、モデルの取得から量子化、サーブまで自動的に行われる。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **LM Studio**: 最小。内蔵のモデルブラウザで Hugging Face から直接検索してダウンロードできる。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **llama.cpp**: 中程度。GGUF形式のモデルファイルを別途入手し、パスを指定して起動させる必要がある。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **vLLM**: 中程度。Hugging Face の safetensors 形式や AWQ, GPTQ 形式などを利用する。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]

## 推論速度
- **vLLM**: 極めて高速（同時リクエスト時）。PagedAttentionと連続バッチ処理により、Ollamaの約16〜20倍の同時スループットを達成できる。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **Ollama**: 高速（単一ユーザー時）。Apple Silicon環境では MLX への最適化により、デコード速度が大幅に向上している。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **LM Studio**: 高速。連続バッチ処理などの機能により、単一ユーザー環境で効率的な速度を実現する。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
- **llama.cpp**: 標準的。Ollamaのベースエンジンであるため、同等の基本速度を持つ。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]

## 結論：Ollamaは'mu'に適しているか
Ollamaは、開発者がローカルでプロトタイピングを行う場合や、OpenAI互換APIを利用したエージェント構築を行う場合に最適である。特にセットアップの容易さとモデル導入の手間が最小であるため、迅速な導入が求められる 'mu' の環境において非常に適していると判断する。ただし、将来的に同時接続ユーザー数が大幅に増加し、高いスループットが求められるプロダクション環境へ移行する場合は、vLLM への切り替えを検討すべきである。 [https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/]
