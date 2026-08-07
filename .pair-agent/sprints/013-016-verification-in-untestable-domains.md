# スプリント013〜016 — テスタブルでない領域での検証 実装記録

- 期間: 2026-08-06〜07
- 合意: [013](../agreements/013-roles-verifier-first.md) / [014](../agreements/014-failure-feedback-and-dependency-direction.md) /
  [015](../agreements/015-llm-judge-and-unverified-visibility.md) / [016](../agreements/016-input-protection-two-layers.md)
- 走行記録: `runs/2026-08-06-013/` `runs/2026-08-07-014/` `runs/2026-08-07-015/` `runs/2026-08-07-016/`
- ビジョン記録: `~/.claude/pair-agent/vision/013-016-verification-in-untestable-domains.md`
- コミット: `d8308fe` `a2bf52c` `16f6e2d` `0b9cccb` `2c6237b` `ea8d050` `b71e0d3` `f0afce2`

## 主題 — 012 の「検査器が成果物になった」への対処が、4本かけて別の問題に着地した

各スプリントの結論が次の問いを生み、最後は**検証観そのもの**の更新に至った。

| # | 仮説 | 実走で分かったこと |
|---|---|---|
| 013 | ロール定義で「検査器を先に作って凍結」できる | 計画は効いた（PjM が順序を守った）。**凍結は守られず 29回書き換え** |
| 014 | NG 理由が届かない＋依存伝播の逆流が原因 | 当たり。**29回→1回**。凍結機構は**不要**と判明。代わりに「先に作った検査器は中身を検査できない」（Tool1 事件）が露出。コーディング走行が収束不能に |
| 015 | そもそも正しい検査器は作りうるのか | **接地できる性質だけ**。接地できないものは文脈非共有の LLM 判定者（judge）へ。リサーチ側は狙いどおり |
| 016 | 入力という原本は二層で守る | 防げた。**014/015 の収束不能まで解消**（1周473秒で完遂） |

## 成果（コード）

| 対象 | 変更 |
|---|---|
| `roles/pjm.md` | VERIFIER FIRST を「**接地可能な性質 かつ 既製手段が無い**」に限定 |
| `roles/pdm.md` | criteria の接地を課す。落とせないものは `run` を空に（stand-in check は無検査より悪い） |
| `roles/qa.md` `implementer.md` | `judge` の使い方。中間メモを別ファイルに書かない |
| `mu/process.py` | 依存伝播を**後続方向に限定**（逆流の停止）／`last_failure` の保持と `clear_failure` |
| `mu/l3.py` `l4.py` `l5.py` | 検査 NG の**事実**を実行者へ届ける／`guard`（周ごとの原本検査で即 escalate）／`unverified` の可視化 |
| `tools.py` | **`judge`**（文脈非共有の LLM 検査器）／`protect` の OS レベル保護と属性復元 |
| テスト | 215 → **230 green**（`tests/test_process.py` 新設を含む） |

## 転回点 — 師匠の「テスタブルは例外」

015 の起点になった問い「そもそも論理的に正しい検査機を作りうるのか？」の出所を、
振り返りで尋ねた:

> もともと完成品がテスタブルであることは現実の仕事ではめったにない。そもそも回答が無いことの
> 方が多い。なのでテスタブルで決定的に検証できるという前提自体のそもそも違和感があったのです。
> プログラムコードは決定論の産物なので当然テスタブルですが、それ以外ではほぼすべて
> テスタブルではないはずだからです。

AI は「接地できる性質と接地できない性質がある」と**並列**に整理していたが、**主従が逆**だった。
**接地できない方が普通で、コードが例外**である。含意:

- 決定論の床は「汎用の基盤」ではなく、**例外的に恵まれた領域でだけ手に入る道具**
- **judge が汎用で、check が特殊**。汎用エージェントを名乗るなら判定の既定は判定者側
- 検証は「答えとの照合」ではなく**性質の吟味**（現実は答えを知らないから始まる）

## judge の設計と実測

- **文脈非共有が本体**。渡すのは要件と対象の中身だけ（messages は system と user の2枚）
- **既定を fail 側に**置き、成果物からの**逐語引用**を要求する
- 構造化出力に依存しない（実測で `gemma4:31b-cloud` は `format=` を守らない）。
  JSON でも散文でも読む（装飾許容・判定語は厳格）
- **同一モデルで 5/5 正判定**（`qwen3.5:9b` も 5/5）。014 で決定論 check が通してしまった
  placeholder ケースを両モデルとも fail と判定した
- 実走で QA が「各主張に出典 URL があるか」の FAIL を根拠に `ACHIEVED: no` を書いた——
  決定論 check は `http` が1本あれば ok を返しており、**judge がその穴を捕まえた**

## Skill

- 新規: [[testability-is-the-exception-not-the-rule]]（confirmed・師匠の視座）/
  [[suspect-the-mechanism-before-blaming-the-norm]]（forming）/
  [[protect-the-original-in-two-layers]]（confirmed・師匠の明示）
- 更新: [[verifier-must-not-be-writable-by-the-verified]]（**当時の対処案「凍結」が実走で
  否定された**経緯ごと書き換え）/ [[external-failure-needs-control-group-and-repetition]]
  （走行の結論には「1走の観察である」と書く）

## 残課題

- **QA が判定書を完成できない**（4走連続）。権限拒否 32→19→15 と漸減するが解けていない。
  作業場（`write_scope` の scratch）は機構で解くしかない
- **PdM のマーカー言語依存**（ロール定義では直らなかった）
- **未検査の可視化**は入ったが、PdM が全基準に `run` を付けたため**まだ実証されていない**
- `gemma4:31b-cloud` が構造化出力を守らない件（既存の層も同じリスクを負う）
