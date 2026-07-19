---
name: ツール dispatch はモデル引数を関数シグネチャに束縛する
description: 厳格な func(**args) はモデルが幻覚した未知引数1つで正しい呼び出しごと落とし、弱いモデルを無限ループに増幅する。dispatch は引数をシグネチャに束縛し未知kwargを落として注記する。
type: process
maturity: confirmed
---

ツール dispatch は「モデルが吐いた引数をそのまま `func(**args)` に渡す」を避ける。引数を**関数シグネチャに束縛**し、シグネチャにない kwarg は落として結果に注記する。厳格な `func(**args)` は、モデルが幻覚した**余計な1引数**で、中身が正しい呼び出しごと `TypeError` にして落とし、弱いモデルを無限ループへ増幅する。

**Why:** mu / L3（2026-07-19）。師匠の実行ログで機序が確定。qwen3.5:9b が `write_file` に存在しない `content_type` を幻覚して付け続け、L1 の `_invoke` が `func(**args)` で `TypeError` にして無限ループ化した（`path`/`content` は正しく、`content_type` を落とした周は現に成功）。**厳格な dispatch がモデルの些細な幻覚を致命化していた** ＝ 師匠の「ハーネスの弱さが差につながった」の指摘が的中（[[master-doubt-is-bug-signal]]）。方針a で `_invoke` を `_bind_to_signature` によるシグネチャ束縛に修正（commit `c4978d0`、TDD・全50 green）。

**How to apply:**
- `inspect.signature` でパラメータに束縛し、未知 kwarg は落として結果に注記する（透明化＋モデルへの弱い steering）。`**kwargs` を受ける関数はそのまま通す。
- 落とした後に**本当に必須引数が欠けていれば従来どおりエラー**を返す（頑健化であって、正しさの検査は捨てない）。
- これは「渡されたツールを頑健に回す」というハーネス本来の責務の**バグ修正**であって、新しい recovery 機構ではない（[[ask-existing-structure-before-adding-mechanism]] の境界内）。低レイヤに retry を二重実装しない（[[failure-needs-analysis-not-blind-retry]]）。
- 一般化: 弱いモデルの出力ブレは、厳格な境界（`**args`・厳格 JSON・厳格パス）で「致命化」しやすい。境界を頑健にするとモデル差が「致命」から「生存可能」に変わる。ただしモデル側の本質的弱さ（自己修正不能・中身の質）は harness では治らない → capable モデルを既定に（[[multi-model-reference-avoid-overfit]]）。
- 関連: [[master-doubt-is-bug-signal]] / [[ask-existing-structure-before-adding-mechanism]] / [[failure-needs-analysis-not-blind-retry]] / [[environment-grounding-is-caller-concern]] / [[multi-model-reference-avoid-overfit]]
