# LONGTERM TODO

長期の改善タスクリスト。出典は実装レビュー [docs/review-2026-07-20.md](docs/review-2026-07-20.md)（項番 A/B/C/D はレポート内の見出しに対応）。
着手時はスプリントとして協議してから進める。

**2026-07-20 処理**: 下記のうち「実機の genuine failure が必要な `_ANALYZE_SYSTEM`」と「L4 着手時に検討と規定した L3 step 面」を除き、全項目を実装・検証済み（テスト 71 green、live 含む）。

## 優先度: 高

- [x] **README を L3/北極星到達後の姿に更新**（[A-1](docs/review-2026-07-20.md#a-1-readme-が実装に対して2スプリント分古い既知の残タスクの確認)）— 2026-07-20 完了
  - L3 の節・層テーブル L3/L4 行・`l3_chat.py` の使い方・決定事項（L3/北極星/テスト数）を反映
  - 「外部依存ゼロ」の文言を実態（依存最小＝`ollama`＋`httpx`）に修正（[A-2](docs/review-2026-07-20.md#a-2-三原則の外部依存ゼロが自己矛盾)）
- [x] **L0: connect タイムアウトを設定する**（[B-1](docs/review-2026-07-20.md#b-1-l0-タイムアウトが実は存在しないreadme-との齟齬)）— 2026-07-20 完了
  - 既定クライアントに `httpx.Timeout(None, connect=5.0)`（`connect_timeout` 引数で調整可）。read は生成を切らないため無制限のまま
- [x] **l1_chat: ループ上限を規定する**（[B-2](docs/review-2026-07-20.md#b-2-l1_chat-ループ上限が無い実証済みの無限ループ経路が開いたまま)）— 2026-07-20 完了
  - `MAX_ROUNDS = 32` を CLI 側で規定し、上限到達時は打ち切りを表示

## 優先度: 中

- [x] **L0: 自動 pull にリトライを付ける**（[B-3](docs/review-2026-07-20.md#b-3-l0-自動-pull-にリトライが無い)）— 2026-07-20 完了。接続系（ConnectionError / TransportError）のみ chat と同じバックオフで吸収、レジストリ失敗はリトライしない
- [x] **l1_chat / l2_chat の docstring 更新**（[C](docs/review-2026-07-20.md#c-ドキュメントの抜け不整合コード内)）— 2026-07-20 完了（9b・5種・上限の記述）
- [x] **テストの抜けを埋める**（[D](docs/review-2026-07-20.md#d-テストの抜け)）— 2026-07-20 完了（17件追加・全71 green）
  - [x] L3: max_rounds 到達後の最終 overall 判定の経路（合格/不合格の両方）
  - [x] L3: 全単位 done → overall 不合格 → 再計画の else 分岐
  - [x] L3: Plan が空（`units:[]` / `{}`）の縮退経路
  - [x] L2: `[L2] ` フィードバックが次の Reflect transcript から除外されること
  - [x] L1: 1応答に複数 tool_calls
  - [x] L0: `show()` / `list()`（allow_pull=False 経路）＋connect タイムアウト既定値
- [ ] **`_ANALYZE_SYSTEM`（失敗分析プロンプト）を genuine failure で詰める** — 合意004の積み残し（[E-6](docs/review-2026-07-20.md#e-改善提案優先順)）
  - ※実機で本物の失敗を観測しながら詰める作業のため未処理。l3_chat での実走（師匠同席の HITL）が必要
  - 準備済み: 失敗する題材セット＋評価シート → [docs/analyze-probe-set.md](docs/analyze-probe-set.md)（2026-07-20）

## F1-g 実走（2026-07-20）で確定した修正候補

出典: [docs/analyze-probe-set.md](docs/analyze-probe-set.md) の「実施記録 F1-g」。

- [x] **[重大] `_carry_done` の同一ファイル穴（偽・完遂）** — 2026-07-20 修正済み。Plan/Replan プロンプトに「file はプラン内で一意」ガードを追加し、`_carry_done` は重複 file の done を引き継がない防御に（TDD・3件追加・全73 green）
- [x] **pytest が temp/ の生成物テストを収集する問題** — 2026-07-20 修正済み。`testpaths=["tests"]` で収集範囲を限定（従来の green 数には temp/ の残骸が混入していた）
- [ ] **証拠デッドロック** — `read_file` の4000字截断×transcript の6000字上限で、大きいファイルの「全文提示」が原理的に不可能。Reflect を実行ベースの証拠へ誘導する／Plan に「機械可読な合格出力（例: `12/12 passed` を印字）」を criterion として要求させる
- [ ] **必須引数欠けエラーの steering** — `_invoke` の TypeError 時に usage_text を添えて返す（F1-g / F1-g2 とも `write_file` の path 欠けが十数回連続・自己修正できなかった。実時間の最大の浪費源）

## F1-g2 再走（2026-07-20）で確定した修正候補 — 「静かに成功を報告する」バグ

`_carry_done` の穴と同じクラス（偽・完遂）。**着手前に [docs/experiment-2026-07-20-f1.md](docs/experiment-2026-07-20-f1.md) を読むこと** — 4件の偽陽性を統一的に診断し（「判定が実体でなく表象に対して行われている」）、対処前に考えるべき問い7点を挙げている。師匠の指示によりクールダウン中で、**個別に慌てて潰さない**。

- [ ] **[重大] L2 Reflect が「書かれていないファイル」を pass させる** — 走行2の単位2は `write_file` が path 欠けで4連続失敗しファイルを一度も更新できなかったのに `passed=True`（`list_dir` は前後とも 3200 bytes）。Reflect は transcript 上の「提案されたコード」を証拠に採用し、ディスクの実体を見ていない。tool の error 行は同じ transcript 内にあった
- [ ] **[重大] 要件がプランを通り抜けて失われる** — 再計画の criterion がゴール9機能のうち7つしか列挙せず、期限・優先度が脱落。L2 Reflect は criterion に対して判定するため、落ちた要件は検査対象外になる。対策候補: Plan/Replan プロンプトに「criterion はゴールの要件を漏れなく含めよ」を課す／L2 へ渡す unit goal に元ゴールを添える（現状は task/file/criterion のみ）
- [ ] **[重大] overall が欠落要件を幻覚で埋める** — `_OVERALL_SYSTEM` は GOAL を持ち scope 完全性を判定する役目なのに、実在しない deadline・priority を「含む」と明示して passed=True を返した。「`[x]` を信頼しファイル内容を見るな」の指示が強すぎ、criterion に無い機能まで信頼している。対策候補: 「unit の task/criterion に現れない要件は present とみなすな。ゴールの要求を1つずつ criterion と照合せよ」を追加
- [ ] **[調査] 長文脈でツール引数の忠実度が落ちる仮説** — 各単位の初回書き込みは成功し周を重ねると path 欠けが連続、再計画後の新規 L2 実行（messages リセット）では 8355 字を一発成功。「content が長いほど失敗」との切り分けが未実施

## 優先度: 低（設計論点・小さな穴）

- [ ] **L3 の中断・再開の対称性**（[A-3](docs/review-2026-07-20.md#a-3-l3-だけ中断再開の対称性が無い)）— L1/L2 の `step()` に相当する面を L3 にも。※本リストの規定どおり L4 着手時にまとめて検討
- [x] **L3: `max_rounds` と単位数の暗黙制約**（[B-4](docs/review-2026-07-20.md#b-4-l3-max_rounds-が単位数を暗黙に制約する)）— 2026-07-20 完了。返り値に `rounds` を追加し（上限到達＝`done=False` かつ `rounds==max_rounds` を判別可能に）、l3_chat の未達表示にも周回数を出す。上限の比例スケールは採らず「上限は呼び出し側が規定」を維持
- [x] **L0: 408/429 の扱い**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。408→リトライ後 `Unreachable`、429→リトライ後 `ResourceExhausted`
- [x] **L1: system 二重注入の併合**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。呼び出し側の先頭 system と1枚に併合（永続 messages は不変）
- [x] **L2: verdict `next` が空文字のときのフォールバック**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。`_NEUTRAL_NEXT`（証拠提示への中立指示）へ
- [x] **l3.py の `_transcript` 私的 import 解消**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。`transcript` として公開化（L2 Reflect と L3 失敗分析が共用する旨を docstring に明記）
- [x] **pyproject に `httpx` を宣言**（[A-2](docs/review-2026-07-20.md#a-2-三原則の外部依存ゼロが自己矛盾)）— 2026-07-20 完了
