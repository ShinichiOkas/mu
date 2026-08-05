# スプリント008 — L4 のコアをミニマイズ 実装記録

- 期間: 2026-08-04〜（実行中）
- 合意: [../agreements/008-l4-core-minimize.md](../agreements/008-l4-core-minimize.md)
- ビジョン: 師匠「L4 のコードは**役割定義を読んで着せ、決定論の床を回すだけ**」

## 仕分け一覧 — コアに残ったものはすべて「不変」か

外出しの基準は [[externalize-only-what-varies-by-use]]:
**用途で変動する値は外、システムが稼働するための普遍の値はコアに残す。**

### 外へ出したもの

| 出したもの | 行き先 | なぜ変動するか |
|---|---|---|
| PdM の生命線プロンプト（specify / respecify） | `roles/pdm.md` | 何を仕様と呼ぶか・どこまで厳しく定義するかは用途次第 |
| PjM の生命線プロンプト（process / decide） | `roles/pjm.md` | プロセスの編み方・再実行の判断基準は用途次第 |
| architect / implementer / qa の職掌 | `roles/*.md`（006 から） | 同上 |
| 役割の権限宣言 | `roles/*.md` frontmatter（007 から） | 現場ごとに変わる |
| QA タスクの文面・出力ファイル・成功条件 | `roles/qa.md` frontmatter（上書き値） | 判定書の名前や粒度は用途次第 |
| artifact の注記 | `## spec-artifact` / `## process-artifact` | 人間向けの案内文は現場ごとに変わる |
| **役割定義の読み込み・節の取り出し・権限適用** | `mu/role_kb.py`（層の外の facility） | **出所（ファイル／DB／API）が変わりうる**（師匠の指摘） |

### コアに残したもの — すべて「不変」と説明できるか

| 残したもの | 行数 | なぜ不変か |
|---|---|---|
| `Director`（run のループ・分岐・生命線呼び出し） | 253 | L4 という層の仕事そのもの。目的→仕様→プロセス→逐次実行→判定→部分再実行の順序は用途で変わらない |
| スキーマ3種（specify / process / decide） | 62 | **ポジションの契約**。コードの分岐が依存する（`feasible=false`→escalate、`action` の enum、task の必須キー） |
| `_shape_line` | 23 | 契約をプロンプトへ供給する機構。スキーマを唯一の出所にするための変換であり、内容を持たない |
| `_VERDICT_CONTRACT` ＋ `_read_verdict` | 27 | 判定書は機械的に読む。**書式と読み手は同じ場所にある必要がある** |
| `_DEFAULT_QA_TASK`（ミニマム）＋ QA 補完 | 20 | 「検証を飛ばして完遂に到達できない」床。文面は上書き可、**存在は不可** |
| `_invalidate` / `_carry_done_tasks` | 47 | 部分再実行の依存伝播と carry 防御。QA を必ず再実行する床 |
| `_normalize_spec` / `_normalize_tasks` / `_normalize_criterion` | 75 | 壊れた LLM 出力を安全側へ落とす床（uncertain / escalate / QA 補完） |
| `_input_grounding` | 30 | 事実は呼び出し側が渡す（LLM に想像させない）という構造上の規律 |
| `_run_criteria_checks` / `_criterion_line` | 22 | 決定論の check。verdict とは独立に走る床 |
| `_write_spec` / `_write_process` | 51 | ファイル・グラウンディング＝層の背骨（**構造**は不変、注記だけ上書き可） |
| `_task_goal` | 33 | タスクへ渡す IN の組み立て（契約・参照ファイル・目的の原文の接地） |
| モジュール docstring | 44 | — |

**判定: すべて「不変」と説明できる。** 用途で変わるものはコアに残っていない。

### 規模の推移

| | 開始時 | Phase1 後 | Phase2 後 | 現在 |
|---|---|---|---|---|
| `mu/l4.py`（層） | 827 | 827 | 880 | **751** |
| `mu/role_kb.py`（facility） | — | — | — | 153 |
| `roles/*.md`（データ） | 76（3件） | 161（5件） | 155 | 155 |

Phase1 でプロンプトを外に出しても**行数は減らなかった**（削れた 72 行と、契約供給・節取り出し・
ミニマム上書きの新機構が同量）。減ったのは Phase2 の facility 化——つまり
**ミニマイズの実体は「プロンプトを追い出すこと」ではなく「層でないものを層から出すこと」だった。**

## 成果（実行中）

- Phase1: PdM/PjM の生命線プロンプトを `roles/` へ。契約（返す形）はスキーマから生成して供給。
  定義書が無ければ「指示なしの役割」として動きログに出す（既定プロンプトへ落ちない）
- Phase2: ミニマム＋上書き（QA タスク・artifact 注記）。判定書の書式はコードが供給。
  役割 KB を `mu/role_kb.py` へ facility 化（**出所は差し替え可能**）
- Phase3: docstring（l4.py / l4_chat.py）・README（構造規約／L4 節／役割の表）を同期、本仕分け一覧
- Phase4: 比較実走（[runs/2026-08-04-008/README.md](../../runs/2026-08-04-008/README.md)）——
  H3 escalate・bugfix/deadstock achieved で**移行は挙動を変えていない**。
  `roles/` 空の対照走は escalate で終わり、**知識が効いていることを実証**
  （知識なしの PjM は `developer` を1人発明しただけ／PowerShell を選択／設計書なし／
  架空の入力 sales_data.csv を生成／判定は契約違反で uncertain）。
  実走で自分の劣化（判定書の REASON が機械読みで空になる）を発見し対処（d4b1a13）

## 持ち越し（このスプリントでは触れない）

- **L4 の責務そのものの見直し**（751 行はまだ突出している。データの外出しでは解けず、
  1層1ファイル原則が言う「責務を見直す」段階の話）
- 並列実行 ／ PjM が QA タスクを複数立てると判定書が割れる ／ PMBOK のリスク領域
