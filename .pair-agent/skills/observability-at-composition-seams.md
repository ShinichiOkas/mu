---
name: 観測点は層に埋めずCLI合成点で外から包んで注入する
description: 実況ログ・計測は mu の各層を変えず、呼び出し側(CLI)が既存のDI合成点で proxy/wrapper に包んで差し込む。観測もまた呼び出し側の責務。
type: process
maturity: confirmed
---

実況・計測（ログ、所要時間、トークン数など）を足すとき、**mu の層（l0/l1/l2/l3）には手を入れない**。呼び出し側（`l{N}_chat.py`）が、既に stack を組み立てている **DI 合成点**で層を proxy/wrapper に包んで観測を差し込む。

**Why:** mu / L3（2026-07-19）。L3 実行中の長い沈黙（ローカル LLM 推論・ツール実行）を可視化する要望に対し、`l3_chat.py` **だけ**で実況を実現した。`l0` を層ラベル付き `_VerboseL0` プロキシで、tools を `_verbose_tool` デコレータで包み、合成点（`ToolLoop(l0)` / `Agent(l0, l1)` / `Orchestrator(l0, l2)`）へ注入。層は無変更。師匠が承認。「環境グラウンディングは呼び出し側」([[environment-grounding-is-caller-concern]]) と同じ非対称が**観測にも及ぶ** — 状態も方針（上限・承認）も環境も観測も、mu の外側が与える。

**How to apply:**
- 観測を足したくなったら、まず「層を変えずに合成点で包めるか」を問う。層に print/log を埋め込まない（無状態・無汚染を保つ）。
- 沈黙の正体（＝時間のかかる箇所）を合成点で特定する: LLM 推論は `l0.chat` の proxy、ツール実行は tool の wrapper。層ごとにラベルを変えると入れ子（L3>L2>L1>tool）が見える。
- ラッパーは `functools.wraps` で `__name__`・docstring・署名を保つ（L1 の dispatch と ollama の関数→スキーマ変換が不変であることをテストで担保する）。
- 関連: [[per-layer-chat-cli]] / [[environment-grounding-is-caller-concern]] / [[minimal-innermost-is-infrastructure]] / [[one-file-per-layer]]
