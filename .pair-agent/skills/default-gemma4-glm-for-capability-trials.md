---
name: 既定は gemma4:31b-cloud、高性能モデルを試すときは glm-5.2:cloud
description: 実験の既定モデルは gemma4:31b-cloud に固定する。能力差を見たいときだけ glm-5.2:cloud を使う。参照を固定しないと構造限界とモデル限界が切り分けられない
type: process
maturity: confirmed
proposed_by: 師匠
confirmed_by: 師匠
created_at: 2026-08-15
---

## 師匠の言葉（原文）

> 今後の実験はgemma4:31b-cloudに戻しましょう。
> デフォルトはgemma4で、高性能モデルを試す時はglmで。

## 適用

- **probe の実走・スモーク・回帰は `gemma4:31b-cloud`**（`probe_standing.py` / `probe_hard.py` の
  コード既定も同じ）
- **`glm-5.2:cloud` は能力差を見る対照のときだけ**。使ったら、比較対象として
  同一条件の gemma4 の走を必ず添える

## Why

- **参照を固定しないと、構造限界とモデル限界が切り分けられない。** mu は L3 の頃から
  この流儀で走っている（README:「qwen3.5:9b は参照として残し、構造限界とモデル限界を切り分ける」）
- 032〜041 の全走が gemma4 なので、**比較の厚みが違う**
- glm-5.2 はこの harness で不安定さを見せた（044: 「適合するパッケージが無い」の誤申告 2/4・
  `unparseable PjM decision` 1/4 ／ 046 R1: 締切 1200s に対して **4330s**）。
  既定に据えると、測りたいもの以外の雑音が増える
- ただし glm は**長文の保存に強い**（040 gemma 24% ↔ 042 glm 92%）。
  そこを見たいときは正しい選択になる → [[model-changes-the-direction-not-the-instrument]]
