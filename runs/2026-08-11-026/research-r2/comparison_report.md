# ローカルLLMランタイム比較報告書

本報告書では、Ollama、llama.cpp、vLLM、LM Studioの4つのツールについて、「リソース消費量」「セットアップ」「API汎用性」の観点から比較し、プロジェクト『mu』のベースとしてOllamaが最適であるかを評価する。

## リソース消費量

| ツール | リソース消費の特徴 | 根拠URL |
| :--- | :--- | :--- |
| **Ollama** | 内部でllama.cppを利用しており、量子化モデル（GGUF等）を用いてメモリ消費を抑える。GPU自動検知機能を備える。 | [docs.ollama.com](https://docs.ollama.com/index) |
| **llama.cpp** | C/C++による最小限の依存関係で実装され、CPU/GPUハイブリッド推論が可能。非常に軽量で、多様な量子化ビット数（1.5〜8bit）をサポートしメモリ消費を極限まで最適化できる。 | [github.com/ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/README.md) |
| **vLLM** | PagedAttentionなどの技術により、高スループットを実現。メモリ効率は高いが、基本的にはサーバー向けであり、単一ユーザーの軽量動作よりも同時リクエスト時の効率に特化している。 | [docs.vllm.ai](https://docs.vllm.ai/en/latest/api/vllm/) |
| **LM Studio** | GUIベースのアプリケーションであり、推論エンジンとしてのリソース消費に加え、アプリケーション自体のオーバーヘッドがある。内部的にGPUオフロード設定が可能。 | [lmstudio.ai/docs](https://lmstudio.ai/docs) |

## セットアップ

| ツール | セットアップコスト | 根拠URL |
| :--- | :--- | :--- |
| **Ollama** | **極めて低い**。インストーラーの実行後、`ollama run <model>` コマンド一つでモデルのダウンロードから実行まで完結する。 | [docs.ollama.com/index](https://docs.ollama.com/index) |
| **llama.cpp** | **中〜高**。ビルドが必要な場合が多く、モデルファイル（GGUF）を別途手動で用意してパスを指定する必要がある。 | [github.com/ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/README.md) |
| **vLLM** | **中**。Python環境（pip/uv）の構築が必要。主にLinux環境を前提としており、CUDA/ROCm等のドライバ設定が必須。 | [docs.vllm.ai](https://docs.vllm.cc/en/latest/getting_started/quickstart.html) |
| **LM Studio** | **極めて低い**。デスクトップアプリをインストールし、GUI上の検索窓からモデルを選択してダウンロードするだけで利用可能。 | [lmstudio.ai/docs](https://lmstudio.ai/docs) |

## API汎用性

| ツール | APIの特徴 | 根拠URL |
| :--- | :--- | :--- |
| **Ollama** | 独自のREST APIを提供しつつ、OpenAI API互換レイヤーを実装しているため、既存のOpenAI SDKを利用した連携が容易。 | [docs.ollama.com/api/openai-compatibility](https://docs.ollama.com/api/openai-compatibility) |
| **llama.cpp** | `llama-server` によりOpenAI互換APIを提供。C++ベースの低レイヤAPIも公開されており、深い統合が可能。 | [github.com/ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/README.md) |
| **vLLM** | OpenAI互換のREST APIを標準提供。高スループットな推論サーバーとしての設計であり、プロダクション環境への適応力が高い。 | [docs.vllm.ai](https://docs.vllm.ai/en/latest/api/vllm/) |
| **LM Studio** | OpenAIおよびAnthropic互換のエンドポイントを提供。SDK（TypeScript/Python）も提供されており、開発者向けの利便性が高い。 | [lmstudio.ai/docs/developer](https://lmstudio.ai/docs/developer) |

## 結論

**Ollamaは『mu』のベースとして最適であると判断する。**

理由は以下の通りである：
1. **開発速度の最大化**: セットアップコストが極めて低く、モデルの管理（Pull/Push/Create）がCLIで完結するため、プロトタイプ開発のサイクルを高速に回せる。
2. **バランスの良いリソース効率**: llama.cppを内部で利用しているため、個人のPC環境（CPU/GPU）でも十分に動作する軽量性を維持している。
3. **高いAPI互換性**: OpenAI API互換レイヤーを持つため、将来的にクラウドLLMへの切り替えや、エコシステムにある多様なツールとの連携が容易である。

vLLMは高負荷サーバー向け、LM StudioはGUI完結の個人利用向け、llama.cppは極限の最適化・制御向けであるのに対し、Ollamaは「使いやすさ」と「エンジンの強力さ」を高い次元で両立しており、アプリケーション基盤としてのバランスが最も優れている。
