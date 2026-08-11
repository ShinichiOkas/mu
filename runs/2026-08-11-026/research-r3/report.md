# ローカルLLM実行基盤 比較報告書

本報告書では、ミニマルな汎用エージェント『mu』の基盤として、Ollamaを継続利用すべきかを判断するため、主要なLLM実行基盤（Ollama, llama.cpp, vLLM, LM Studio）を4つの観点から比較分析します。

## 比較一覧表

| 観点 | Ollama | llama.cpp | vLLM | LM Studio |
| :--- | :--- | :--- | :--- | :--- |
| **導入コスト** | 極めて低い（簡単） | 低い（ポータブル） | 中〜高（サーバー向け） | 極めて低い（GUI） |
| **リソース効率** | 高い（ローカル最適化） | 極めて高い（量子化） | 最高（スループット重視） | 高い（GUI設定可能） |
| **拡張性** | 高い（REST API/SDK） | 極めて高い（バックエンド多） | 高い（HF連携/ライブラリ） | 高い（SDK/API） |
| **運用安定性** | 高い（Docker対応） | 極めて高い（多様なHW） | 高い（商用スケール） | 高い（headless対応） |

---

## 詳細分析

### 1. Ollama
- **導入コスト**: ローカル展開に特化しており、クラウドAPIコストを削減でき、個人利用において無料かつオープンソースで提供されている。
  - 出典: https://ollama.com/
- **リソース効率**: ローカルでの効率性を追求し、AMD GPU (via ROCm) や Apple Silicon を含む多様なハードウェアをサポートしている。
  - 出典: https://docs.ollama.com/linux
- **拡張性**: REST API および Python/JavaScript の公式ライブラリを提供しており、他アプリケーションへの統合が容易である。また、「Modelfile」によるモデル構成の定義が可能である。
  - 出典: https://docs.ollama.com/index
- **運用安定性**: Docker によるデプロイをサポートしており、異なるプラットフォーム間で一貫した環境を構築できる。
  - 出典: https://deepwiki.com/ollama/ollama/6.3-docker-deployment

### 2. llama.cpp
- **導入コスト**: 依存関係のない C/C++ 実装であり、セットアップコストが最小限で、ローカルおよびクラウドへの移植性が非常に高い。
  - 出典: https://github.com/ggml-org/llama.cpp
- **リソース効率**: GGUF 量子化（1.5-bit 〜 8-bit）により極めて効率的であり、CPU+GPU のハイブリッド推論によって VRAM を超えるサイズのモデルも動作可能である。
  - 出典: https://github.com/ggml-org/llama.cpp/blob/master/README.md
- **拡張性**: CUDA, Metal, HIP, Vulkan, SYCL など多数のバックエンドをサポートし、OpenAI 互換 API へのアクセスを可能にする HTTP サーバーを内蔵している。
  - 出典: https://github.com/ggml-org/llama.cpp/blob/master/README.md
- **運用安定性**: Apple Silicon, x86 (AVX/AMX), RISC-V など、極めて広範なハードウェアで堅牢なパフォーマンスを発揮する。
  - 出典: https://github.com/ggml-org/llama.cpp/blob/master/README.md

### 3. vLLM
- **導入コスト**: スループットを最大化することでリクエストあたりのコストを削減することに重点を置いた、本番環境向けサーバーとしての導入が主となる。
  - 出典: https://vllm.ai/
- **リソース効率**: **PagedAttention** により KV キャッシュの断片化を排除し、高いメモリ効率と連続バッチ処理による高スループットを実現している。
  - 出典: https://docs.vllm.ai/en/latest/design/paged_attention/
- **拡張性**: Hugging Face とのシームレスな連携に加え、GPTQ, AWQ, FP8 などの多様な量子化スキームをサポートする高性能サービングライブラリとして設計されている。
  - 出典: https://vllm.ai/
- **運用安定性**: CUDA/HIP グラフのサポートや分散デプロイメント機能など、プロダクションスケールでの運用を想定して設計されている。
  - 出典: https://docs.vllm.ai/en/latest/

### 4. LM Studio
- **導入コスト**: ローカルファーストのプラットフォームであり、ユーザー自身のハードウェアでモデルを動かすことでクラウドコストを完全に排除できる。
  - 出典: https://lmstudio.ai/docs
- **リソース効率**: GUI による設定が可能であり、最適化手法を用いて応答時間とメモリ効率を向上させている。
  - 出典: https://deepwiki.com/lmstudio-ai/docs/7-advanced-features
- **拡張性**: TypeScript および Python SDK、CLI ツール (`lms`) を提供し、OpenAI/Anthropic 互換の REST API エンドポイントを備えている。
  - 出典: https://lmstudio.ai/docs/developer
- **運用安定性**: `llmster` によるヘッドレスデプロイをサポートしており、GUI なしでサーバーやクラウドインスタンス上でデーモンとして実行可能である。
  - 出典: https://lmstudio.ai/docs/developer

---

## 結論

### mu の基盤としての判断基準
『mu』は「きわめてミニマルな汎用エージェント」であるため、以下の条件を重視します：
- **セットアップの容易さ**（導入コストの低さ）
- **低リソースでの動作**（リソース効率の高さ）
- **外部ツールとの連携容易性**（拡張性の高さ）

### 判断結果
**Ollama を使い続けるべきである。**

**根拠:**
1. **導入コスト**: llama.cpp や LM Studio と同等に低い導入コストを実現しており、特に「モデルの管理と実行」がパッケージ化されているため、ミニマルな構成を維持しやすい。
2. **リソース効率**: ローカル最適化が進んでおり、Apple Silicon や AMD GPU などの多様な環境で効率的に動作する。
3. **拡張性**: REST API および公式 SDK が整備されており、エージェントとしての外部ツール連携を実装する上でのオーバーヘッドが極めて少ない。
4. **運用安定性**: Docker サポートにより、開発環境から実行環境への移行が容易である。

vLLM は高性能だがサーバー志向が強く、llama.cpp は極めて効率的だがセットアップに一定の知識を要し、LM Studio は GUI 依存が強い（headless はあるが）。Ollama はこれらの中間で、「使いやすさ」と「エンジニア向けの柔軟性」を高い次元で両立しており、ミニマルな汎用エージェントの基盤として最適であると判断します。
