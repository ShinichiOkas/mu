# 走行記録 2026-08-10-021 — 再現率と汎用性の測定（難課題9種＋schedule 3条件比較）

コマンド: `MU_TIME_BUDGET=3300 probe_hard.py <case> gemma4:31b-cloud runs/2026-08-10-021/<dir> qwen3.5:9b`（逐次）

## 総括

- **偽・達成はゼロを維持**（全11走。通算記録は 019 以降の全走で継続）
- **課題9種のうち8種で正しい結果**（achieved 7種＋contradiction の正しい escalate）
- 唯一の失敗（schedule）は**偽・不合格**（安全側）で、原因2件を特定・修理し、
  修理後の再測で **achieved**。3条件比較で修理の因果も分離できた
- 新発見の重大穴: **L0 の read タイムアウト無制限**（cloud ストールで110分の無音ハング。
  deadline は協調的で救えない）→ LONGTERM_TODO [重大]

## 本測定（9走）

| # | 課題 | 結果 | 時間 | 実体確認 |
|---|---|---|---|---|
| 1 | deadstock-r1 | achieved ✓ | 711s | 報告書 P007/P010（正解） |
| 2 | deadstock-r2 | achieved ✓ | 159s | 報告書 P007/P010（正解）。**019p6 と合わせ3連続達成＝再現** |
| 3 | jsonparse | achieved ✓ | 271s | セルフテスト JSONPARSE OK 実出力 |
| 4 | contradiction | **escalate ✓（正解）** | **2s** | PdM が矛盾2制約を原文引用して充足不能を申告（007 三重ガード再検証） |
| 5 | sitegen | achieved ✓ | 601s | site/ 4ページ生成・保護入力 md_src/ 無傷 |
| 6 | bugfix | achieved ✓ | 61s | **観測者が test_stats.py を独立再実行して OK**・テスト無傷 |
| 7 | perf | achieved ✓ | 218s | ANALYZE OK 0.36（要件3秒） |
| 8 | schedule | **偽・不合格**（下記） | 705s | 実体は完璧（正解枠 MTG-001 予約・QA yes）だが機械検査 NG で escalate |
| 9 | action | achieved ✓ | 322s | maintenance_state.json = mode:full・4工程（-Mode full を自力発見） |

新型課題の所見: **サービス越しの状態変化**（schedule）も**成果物を作らない実行終端**（action）も
層構造は適応した。action ではファイル・グラウンディングが証跡ファイル（実行ログ・状態 JSON）を
足がかりに自然に成立。schedule の失敗は課題の型ではなく検査の接地の問題だった。

## schedule の3条件比較（修理の因果分離）

| 条件 | PdM の検査コマンド | 結果 |
|---|---|---|
| v1: 旧規範・静かなモック | `list` を発明 → モックがヘルプ＋exit 0 → **静かに壊れ、ヘルプ文面と偶然一致した偽 PASS 混在** | 偽・不合格（escalate・実体は完璧） |
| v2: 旧規範・大声モック（対照） | `list` を発明（**3走連続**）→ 大声 NG。PjM は原因を言語化しつつ rerun→replan と迷走（respec に行けない）| L0 ハングで打ち切り（下記） |
| v3: 新規範＋自己記述の全文接地・大声モック | **実在コマンドのみ**（bookings ×5・busy ×5・book。`list` は0回） | **achieved: true**（862s・検査4/4 [ok]・violations なし） |

修理3件（コミット `5a23b00`）: ①pdm.md「見た形だけを使う」 ②`_input_grounding` が
スクリプトの自己記述（docstring/コメント塊）を全文接地 ③pjm.md「検査コマンド自体の故障は
respec」＋ escalation_reason の結果契約追加。**「発明を禁じる」と「発明の必要を消す」の
二段構え**（抜粋算術と同じ型）が3走連続の発明を止めた。

モック側の欠陥（未知コマンドにヘルプ＋exit 0）も修理（コミット `397b5c5`）——
自作の計測器が [[denial-must-carry-the-norm]] に違反していた実例。

## 新発見: L0 の無音ハング（v2 打ち切りの理由）

v2 は3周目の途中で **110分以上の無音ハング**（ログ更新なし・CPU ほぼゼロ）。
L0 の read タイムアウトは「ローカルの長い生成を切らない」ため無制限だが、cloud モデルでは
ネットワークストールと区別できない。**deadline はタスク境界でしか見ない協調的機構**なので、
チャット呼び出しの内側では発火できない——外部 kill しか手が無く finally も飛ぶ
（018 で潰した観測ゼロ問題の別入口）。LONGTERM_TODO に [重大] で記録。
