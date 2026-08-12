# 030 実走記録 — needs 宣言と作業空間の分離（2026-08-12）

合意 [030](../../.pair-agent/agreements/030-needs-and-workspace.md) フェーズ C の検証。
確かめたのは3つ——**needs（入力の宣言）を PjM が実際に書くこと**・**tray（作業空間の分離）の
もとで従来の課題が達成できること**・**宣言グラフが完全であること**（read 拒否と needs 未充足の
観測数）。

実験条件は 029 と同一: 課題は coding の `bugfix`（保護入力 `test_stats.py` を1文字も変えずに
`buggy_stats.py` を直す）＋依存連鎖・保護入力3本の `deadstock`。`MU_TIME_BUDGET=1500`・
QA プール `qwen3.5:9b`・**tray 有効（`MU_WORKSPACE` 既定）**。

## 1. 結果の一覧

| 走 | model | achieved | 所要 | 備考 |
|---|---|---|---|---|
| bugfix r1 | gemma4:12b | **true** | 1003s | 二重入れ子の病理を観測（下記 3） |
| bugfix r2 | gemma4:12b | **true** | 336s | C1 修正後。入れ子ゼロ |
| bugfix 31b | **gemma4:31b-cloud**（029 の基準計測器） | **true** | **198s** | **028 の同条件基準 198s と同速＝低下なし**（029 の 105s は同課題の最良値） |
| deadstock | gemma4:12b | **true** | 669s | 依存連鎖＋保護入力3本 |

全走で: 偽・完遂なし・protection violations **none**・保護入力は無傷・判定書は実体
（テスト実行出力・read_file の実読）に接地した本物。

## 2. needs と発行の観測 — 宣言グラフは完全だった

| 観測 | bugfix r2 | bugfix 31b | deadstock |
|---|---|---|---|
| PjM の needs 宣言 | 全タスク（外部・改稿の自己 needs 含む） | 全タスク | 全タスク（保護入力3本を明示宣言） |
| needs 未充足（ゲート発火） | 0 | 0 | 0 |
| needs 未宣言の言及（lint） | 0 | 0 | 0 |
| 発行（publish-out） | 3/3 | 4/4 | 5/5 |
| 発行拒否 / single-writer 違反 | 0 | 0 | 0 |
| tray 外の拒否 | 2 | 4 | 8 |

- **PjM（12b / 31b とも）は skill `declare-task-needs` の装備だけで、初回から needs を
  正しく書いた**。書き漏らし（lint 発火）はゼロ——「宣言グラフ完全」が実走で成立。
- tray 外の拒否はすべて「共有 cwd の絶対パス・`..` での読み書き」を steering で tray に
  戻した場面で、全走とも回復して完遂した。未宣言の依存の混入はゼロ。
- deadstock では PjM が保護入力（inventory.csv / sales.csv / returns.csv）を needs に
  明示宣言し、タスクは**写し**の上で作業した——原本保護が構造で効いている。

## 3. r1 で観測した病理と修理（C1）

r1（1003s）の主因は速度ではなく正しさの欠陥だった（[[correctness-repairs-are-the-best-speedup]] の型）:
モデルが tray 案内を見て**共有 cwd 起点の相対パス**（`.mu-work/<role>/task-N/file`）で書き、
tray 起点解決で**二重入れ子**（`tray/.mu-work/.../file`）に配置された。tray 内なので拒否されず
（観測に出ない誤配置）、成功条件の検査が見つけられず Reflect の書き直しループが回った。

修理は規範でなく機構（C1・[a22b14f]）: 共有 cwd 起点の解決が tray 内に落ちる相対パスは
それを意図とみなす。**どちらの解釈でも採るのは tray 内だけ**なので閉じ込めは弱まらない
（他タスクの tray は名指しできないことをテストで固定）。r1 → r2 で 1003s → 336s、
ツール呼び出し 188 → 94、入れ子ゼロ。

## 4. 12b の残差

12b の 336s は 31b の 198s より遅いが、内訳に病理のループは無い（tray 拒否からの回復
2回と、モデルの逐次的な試行）。tray 導入のコスト（写し・案内文・パス適応）は基準計測器
（31b）では観測されない水準だった。12b の適応はデータが2走しかないので、以後の走で
観測を続ける。
