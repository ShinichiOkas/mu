# 合意 023 — ポリシーレビュー指摘の全消化（クリーンアップ）

status: executing
created: 2026-08-11
approved: 師匠「全部１スプリントにしてください」（2026-08-11。レビュー報告の提案リスト全体への承認）

## 背景

022 までの安定化デバッグでコードが荒れた懸念があり、師匠の依頼で
「ポリシー適合・責務分担・冗長・すっきり」の観点の全体レビューを実施した。
結論: コア（mu/）の骨格（1層1ファイル・依存最小・無状態・判断は外へ・決定論の床）は
維持されており、荒れは CLI/probe の殻と層の継ぎ目のヘルパ置き場に集中。
ただし1件、文書と実装の契約破れ（A1）を発見した。

## スコープ（フェーズ＝コミット単位）

1. **A1** — `role_kb.parse_role_doc` が frontmatter の未知キーを捨てており、
   docstring・process.py・README が約束する「qa の task/file/criterion 上書き」経路が不通。
   未知キーを保持する修理＋**ローダー経由の**回帰テスト（現行テストは dict 手組みで
   declaration-test になっている）。TDD: テストが未修理コードで落ちることを先に確認する。
2. **A2＋C2** — probe_l4 は 016/018 の修理（finally の clear_protection・thaw・guard/deadline）を
   持たない古い殻。f1 / sales ケースを probe_hard の CASES に統合し、probe_l4.py を削除する
   （回避手順を覚えず根絶——structural-duplication-eliminate-not-document）。
3. **B1＋C1** — CLI 実況コード（_VerboseL0・_verbose_tool・_stage・_try_json・_short・_Abort・
   _env_preamble）が l3_chat / l5_chat に二重化し divergence 開始。probe 群と l4_chat は
   l5_chat のプライベート名を import している。共通部を `chat_common.py`（層の外・表示と
   環境接地の共通部）へ抽出し全 CLI/probe が参照する。タワー配線（合成の継ぎ目）は
   各ファイルに明示のまま残す（observability-at-composition-seams）。
4. **B2** — l4 が l3 のプライベート名（_parse_json / _with_env）を import し、
   `structured()`（l4）と `Orchestrator._structured`（l3）が同一実装。l3 側で
   parse_json / with_env / structured を公開名にして一本化。l4 / l5 はそれを使う。
   `lifeline_system` は role_kb 依存なので l4 に残す。
5. **C3＋D** — 小物と残骸:
   - execute_command のインライン一時ファイル保存 → `_save_full_output` を使う
   - `_noop` 3定義 → l3 の公開 `noop` に一本化
   - L5 の時間切れ文言インライン2回 → l4 の `TIME_UP`（公開化）を使う
   - process.py の関数内 `from collections import Counter` → モジュール先頭へ
   - l4.py の孤児コメント（QA ミニマム定義の説明。実体は process.py 移設済み）削除
   - probe_hard.py の存在しない `_place_inputs` 参照を実態に合わせる
   - l4.py の `structured(self._l0, ` 行末スペース・不自然な折り返しの整形
   - `_unit_goal`（l3）と `task_goal`（process）の**文字どおり同一の文面だけ**共有ヘルパ化

## 実行中に採る判断（AI の判断。事後確認対象）

- **probe_l4 は統合のうえ削除**（後始末追加ではなく）。レビュー報告での推奨案を採用。
- **規範文の divergence は強い方（process.py 版）に揃える**。「※ 直すのは成果物の側…」の
  文面が l3 と process で微差（** 強調・一文の有無）。文字どおり同一でない部分の統合は
  行動変化（プロンプト変化）を伴うため、強い方への統一として明示的に行い、ここに記録する
  （dedup-split-defer-behavior-change の記録条項）。
- `_carry_done`（l3）と `carry_done_tasks`（process）は**統合しない**（単位 vs 役割つき
  タスク＝QA 特例のドメイン差。same-shape-different-domain-no-merge）。

## 完了条件

- テストが全 green を維持（フェーズごとに実行。live はスキップ可）
- probe_l4.py が消え、probe_hard で f1 / sales が走らせられる形になっている
- l3_chat / l5_chat / l4_chat / probe_hard / probe_research に実況コードのコピーが無い
- mu/ 内にアンダースコア名の層間 import が無い
- roles/*.md の frontmatter に task/file/criterion を書けば default_qa_task に効く
  （ローダー経由テストで固定）

## スコープ外

- tools.py の3責務分割（意図的同居。並列実行導入時に _PROTECTED グローバル状態を再訪）
- L2/L3 生命線プロンプトの roles/ 外出し（層の機構でありポジションの役割ではない）
- 並列実行・L6
