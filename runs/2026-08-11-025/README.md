# 走行記録 2026-08-11-025 — 025 クローズ前スモーク（性能低下の確認）

コマンド: `MU_TIME_BUDGET=1500 probe_hard.py <case> gemma4:31b-cloud runs/2026-08-11-025/<dir> qwen3.5:9b`（逐次4本）

目的: 025 の挙動変化は **PjM の process プロンプト1点**（役割一覧を人選対象に絞った——
pdm/pjm の行が消えた）。この変更で性能低下が無いことを、021 の基準と同条件で確認する
（師匠の指示によりクローズ前に実施）。課題は PjM の人選・プロセス設計を通る4本を選定:
escalate 経路（contradiction）・コーディング（bugfix）・021 の再現基準（deadstock）・
023 で probe_l4 から統合後の初実走となる保護経路（sales）。

## 結果 — 4/4 期待どおり。性能低下なし・偽・達成ゼロ維持

| 課題 | 結果 | 時間（021 基準） | 実体確認 |
|---|---|---|---|
| contradiction | **escalate ✓ 正解** | 3s（2s） | PdM が矛盾2制約を原文引用して充足不能を申告 |
| bugfix | achieved ✓ | 221s（61s） | test_stats.py 無傷を**ハッシュで**確認・9テスト OK 実出力・QA 別モデル |
| deadstock | achieved ✓ | 1160s（159〜711s） | 報告書 **P007/P010（正解）**・小文字 p008 罠を upper 正規化で処理・**019p6/021 と合わせ4連続達成** |
| sales | achieved ✓ | 143s（—） | 粗利率の実計算で5商品抽出・**保護入力 sales.csv 無傷（violations: none）**——023 統合の実走検証を兼ねる |

## 所見

- **結果の品質に劣化なし。** 全走 protection violations なし。達成判定はすべて実体根拠つき
  （ハッシュ・実行出力・実計算）で、止まるべきものは止まった。
- 時間は cloud の変動の範囲で 021 より遅め。deadstock は L4 3周（verdict.md 単位の失敗
  →再分析→自己回復が1回入った）。021 でも同種の churn は観測されており、致命傷化せず
  回復する挙動は同じ。
- sales が probe_hard の CASES 経由で初めて走り、016/018 の後始末経路
  （finally の clear_protection・thaw）が新しい殻でも機能することを確認した。
