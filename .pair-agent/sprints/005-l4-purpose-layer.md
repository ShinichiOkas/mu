# スプリント005 — L4（目的の層）実装記録

- 期間: 2026-07-21（協議開始）〜 2026-07-31（完了）
- 合意: [../agreements/005-l4-purpose-layer.md](../agreements/005-l4-purpose-layer.md)（v6）
- 実験記録: [../../docs/experiment-2026-07-30-l4.md](../../docs/experiment-2026-07-30-l4.md)
- ビジョン記録: `~/.claude/pair-agent/vision/005-l4-purpose-layer.md`

## 成果

- 構造化 tool 結果（ToolResult: content/ok/facts。実体からの機械可読な事実）— d5fcd2b
- `mu/l4.py`（Director）+ `l4_chat.py`: 目的→操作的定義+完了条件+仕様（SPEC.md artifact）→
  L3→実体ベース3値判定（yes/no/uncertain）。uncertain は escalated=True で人間へ — b880cb2
- L3 overall を機械的照合へ縮小（機序④の温床を除去）— 2ba4afc
- 対処4件（師匠決定スコープ）: 必須引数 steering / criterion 埋め込み check（コード側 verify ゲート）/
  L4 証拠拡張 / truncated 証拠 yes 禁止 — ad3b20b, a0908e9
- テスト 73 → 111 green

## 受入検証（実機 7 走）

- 初回4走: 偽・完遂 3/4 防御、F1×gemma4 で再現（no-op exit=0 + 証拠外挿）→ 対処協議へ
- 対処後2走: 偽・完遂 0/2。no-op exit=0 をコードが名指しで捕捉
- 31b-cloud 比較走: 速度15倍・失敗激減。checks 全通過の成果物から L4 が undo の
  意味レベル欠落を発見して escalate（L4 判定の初実証）

## 学び（Skill 化済み）

- [[verification-needs-visible-output-marker]] / [[llm-pass-needs-code-verify-gate]] /
  [[sprint-acceptance-is-the-observed-failure]] / [[environment-grounding-is-caller-concern]]（精緻化）

## 持ち越し

- L2 の入力データ破壊（LONGTERM_TODO・重大）
- 検証モデル構成の方針（12b + 31b-cloud 案。同一ファミリーの傾向共有リスクは師匠指摘済み）
- L5 / 再入形への畳み込み（決定1: L4 を具体で確かめてから）
