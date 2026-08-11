# ローカルLLM実行基盤 比較報告書

本報告書では、ミニマル汎用エージェント『mu』の基盤として、現在利用している Ollama を継続して利用すべきか、あるいは他の実行基盤（llama.cpp, vLLM, LM Studio）へ移行すべきかを判断するための比較分析を行う。

## 1. 比較概要

以下の5つの観点に基づき、主要な4つの実行基盤を比較した。

| 比較項目 | Ollama | llama.cpp | vLLM | LM Studio |
| :--- | :--- | :--- | :--- | :--- |
| **セットアップコスト** | 極めて低い | 中程度 | 高い | 低い |
| **リソース消費量** | 中程度 | 極めて低い | 高い | 中程度 |
| **APIの互換性** | OpenAI互換 | Serverモードあり | 高性能OpenAI API | OpenAI互換 |
| **モデル管理の容易さ** | 容易 (Docker形式) | 手動 (GGUF管理) | HF Safetensors | 容易 (GUI) |
| **推論速度** | 速い (単一ユーザー) | 速い (基盤エンジン) | 極めて速い (高負荷時) | 速い |

## 2. 詳細分析

### 2.1 Ollama
- **セットアップコスト**: 極めて低い。「1行のインストール」で完了し、設定なしでモデル管理が可能。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **リソース消費量**: 中程度。llama.cpp等のラッパーであるため、Go言語によるオーバーヘッドが存在する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **APIの互換性**: `localhost:11434` でOpenAI互換のREST APIを提供し、多くのフレームワークで利用可能。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **モデル管理の容易さ**: 容易。Dockerライクなコマンド（`ollama pull`）でモデルの取得と量子化の管理を完結できる。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **推論速度**: 単一ユーザー環境では高速だが、高負荷時のスループットはvLLMに劣る。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)

### 2.2 llama.cpp
- **セットアップコスト**: 中程度。Cコンパイラによるビルドまたはバイナリのダウンロードが必要。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **リソース消費量**: 極めて低い。C/C++による最小実装であり、Raspberry Piなどの制限されたハードウェアでも動作する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **APIの互換性**: `llama-server` を提供しており、リバースプロキシ経由で利用可能。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **モデル管理の容易さ**: 手動。GGUFファイルを直接管理し、必要に応じて独自の量子化を行う。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **推論速度**: 高速かつ効率的。OllamaやLM Studioのエンジンとして採用されており、純粋なMetal性能などはラッパー経由より高い。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)

### 2.3 vLLM
- **セットアップコスト**: 高い。Linux環境、Python、および特定のCUDA/ROCmバージョンが必要なDevOps的構築が求められる。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **リソース消費量**: 高い（VRAM消費量）。ただしPagedAttentionによりKVキャッシュの浪費を極限まで抑えている。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **APIの互換性**: 本番環境向けの高性能なOpenAI互換APIを提供し、高並行処理に最適化されている。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **モデル管理の容易さ**: Hugging Faceのsafetensors（AWQ, GPTQ等）を主に使用する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **推論速度**: 極めて速い。継続的なバッチ処理により、高負荷時においてOllamaの16〜20倍のスループットを実現する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)

### 2.4 LM Studio
- **セットアップコスト**: 低い。GUIインストーラーが提供されており、導入が容易。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **リソース消費量**: 中程度。Electron製GUIによるオーバーヘッド（数百MBのRSS）が存在する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **APIの互換性**: OpenAI互換のローカルサーバー機能を提供しており、ヘッドレスモードも利用可能。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **モデル管理の容易さ**: 容易。組み込みのHugging Faceブラウザにより、ハードウェアに最適な量子化モデルを推奨・導入できる。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)
- **推論速度**: 速い。Vulkanサポートが強力で、内蔵GPU等でも効率的に動作する。 [出典](https://codersera.com/blog/ollama-vs-lm-studio-vs-vllm-vs-llama-cpp-vs-mlx-2026/)

## 結論

ミニマル汎用エージェント『mu』の設計思想である**「きわめてミニマル」**に照らし合わせると、以下の理由から **Ollama の継続利用が最適である**と判断する。

1. **導入と管理の最小化**: セットアップコストが極めて低く、`ollama pull` 等の単純なコマンドでモデル管理を完結できる点は、muのシンプルさを維持する上で最大の利点となる。
2. **十分な汎用性**: OpenAI互換APIを備えており、外部ツールやエージェントフレームワークとの連携コストが低い。
3. **リソースのバランス**: llama.cppほどの極小消費ではないが、vLLMのような重厚な環境構築を必要とせず、個人利用レベルの推論速度を十分に提供している。

vLLMはスループットに優れるがセットアップコストが高すぎ、llama.cppはリソース効率に優れるがモデル管理の手間が増える。LM StudioはGUI依存が強く、自動化を前提とするエージェント基盤としてはOllamaに劣る。したがって、運用の容易さと機能性のバランスが最も優れたOllamaを継続して採用することを推奨する。
