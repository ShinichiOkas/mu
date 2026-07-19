# スプリント 004 — l3-global-plan（完了）

- **期間**: 2026-07-04 〜 2026-07-19
- **ゴール**: L3（大域的 Plan / 複雑タスクの完遂）を実装・検証する。P・A は HITL、D・C は自律、ファイル・グラウンディング。北極星＝GUI アプリを自走で完成。
- **結果**: 達成（北極星到達）。

## 成果

- **L3（`mu/l3.py`）** — `Orchestrator`。大域 Plan → 各単位を L2 で完遂 → 全体判定 → 完遂/再計画。P（初回 Plan）・A（再計画）は HITL 承認スロット、D・C は自律。再帰同一構造（L3 の D＝L2）が実機で成立。
- **`l3_chat.py`** — HITL 承認＝人間の CLI（`y` / `d N` / `n`）。各層の実況ログ（LLM 推論・ツール実行の可視化）を CLI 側だけで実装（層は無変更）。環境プリアンブルを L2 へ opaque 転送。
- **生命線プロンプト3件を実タスクで調整** — `_PLAN`（file 必須・run/verify 専用単位の禁止）／`_OVERALL`（`[x]`=done を信頼し scope 判定）／`_REPLAN`（同ガード）。
- **北極星到達** — gemma4:12b で「GUI 付き AI チャットアプリ」を自走完遂。題材は関数電卓でなくとも「GUI アプリの自走完遂」という構造の証明として到達（師匠判断）。
- **既定モデルを gemma4:12b へ** — 同一タスクで gemma 完遂・qwen 不可。2モデル切り分けで完遂できる側へ。
- **L1 ハーネス脆弱性の発見と修正** — qwen の `content_type` 幻覚 × 厳格 `func(**args)` の無限ループを、`_invoke` のシグネチャ束縛（未知 kwarg を落として注記）で解消（方針a）。師匠の「ハーネスの弱さ」の指摘が的中。
- **テスト全50 green**。主な commit: `2ba7d5b`（実況ログ）/ `ba2812b`（既定モデル）/ `c4978d0`（L1 頑健化）/ `e0e99ca`（環境プリアンブル）。

## 振り返り（2026-07-15 / 2026-07-19）

- vision: `~/.claude/pair-agent/vision/mu-004-l3-global-plan.md`（2回分）
- 新規 Skill: `failure-needs-analysis-not-blind-retry` ／ `ask-existing-structure-before-adding-mechanism`（ペア固有）、`observability-at-composition-seams` ／ `tool-dispatch-bind-args-to-signature`（プロジェクト）
- 主な学び: 失敗は分析駆動（機構を反射で足さない）／観測は層でなく CLI 合成点で注入／**師匠の疑問はバグ信号**／bounded probe より実機ログが接地／厳格な境界は弱モデルの幻覚を致命化する。

## 005 への申し送り

1. **【A】GUI の auto/HITL 境界（最重要）** — 実行不能な単位（GUI 等）は Reflect がコード目視で通しており、「完遂 ✓」が GUI の実動を検証していない。合意004 が予告した構造的な崖＝「HITL の粒度」。実行不能単位を人の受け入れに上げる HITL ステップの是非を 005 で設計する。
2. `_ANALYZE_SYSTEM`（失敗分析プロンプト）を **genuine failure** で詰める（004 では判定不能起因の空 analysis しか見ておらず検証が薄い）。
3. README 反映。
- 対象外（無視）: `execute_command` が共有 `.venv` を変更する件（`pip install`）は本テスト環境特有として不対応（師匠判断・2026-07-19）。

## 次スプリント候補（005）

- **GUI の auto/HITL 境界の設計・実装**（上記【A】）を核に。＋ 積み残し（`_ANALYZE_SYSTEM`・README）。
