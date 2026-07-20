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

## 優先度: 低（設計論点・小さな穴）

- [ ] **L3 の中断・再開の対称性**（[A-3](docs/review-2026-07-20.md#a-3-l3-だけ中断再開の対称性が無い)）— L1/L2 の `step()` に相当する面を L3 にも。※本リストの規定どおり L4 着手時にまとめて検討
- [x] **L3: `max_rounds` と単位数の暗黙制約**（[B-4](docs/review-2026-07-20.md#b-4-l3-max_rounds-が単位数を暗黙に制約する)）— 2026-07-20 完了。返り値に `rounds` を追加し（上限到達＝`done=False` かつ `rounds==max_rounds` を判別可能に）、l3_chat の未達表示にも周回数を出す。上限の比例スケールは採らず「上限は呼び出し側が規定」を維持
- [x] **L0: 408/429 の扱い**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。408→リトライ後 `Unreachable`、429→リトライ後 `ResourceExhausted`
- [x] **L1: system 二重注入の併合**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。呼び出し側の先頭 system と1枚に併合（永続 messages は不変）
- [x] **L2: verdict `next` が空文字のときのフォールバック**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。`_NEUTRAL_NEXT`（証拠提示への中立指示）へ
- [x] **l3.py の `_transcript` 私的 import 解消**（[B-5](docs/review-2026-07-20.md#b-5-小さめの問題)）— 2026-07-20 完了。`transcript` として公開化（L2 Reflect と L3 失敗分析が共用する旨を docstring に明記）
- [x] **pyproject に `httpx` を宣言**（[A-2](docs/review-2026-07-20.md#a-2-三原則の外部依存ゼロが自己矛盾)）— 2026-07-20 完了
