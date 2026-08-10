# 合意ドキュメント 022 — L0 の無音ハング修理（read タイムアウトの有限化）

- **sprint**: 022-l0-bounded-read-timeout
- **status**: completed（2026-08-11 完了条件達成・師匠判断で振り返りスキップ。
  ストール模擬で有限時間の Unreachable を実証・308 tests green・コミット 53ac07a）
- **version**: 1
- **前提**: 021 schedule-v2 で [重大] を実測——cloud モデルへの1呼び出しがストールし、
  走行全体が **110分以上の無音ハング**。deadline（018）はタスク境界でしか見ない
  協調的機構のため、チャット呼び出しの内側では発火できず、外部 kill しか手が無かった
  （finally も飛ぶ＝観測ゼロ問題の別入口）。

## 問題の構造

L0 は「ローカル LLM の長い生成を切らない」ため read を無制限にしていた
（`httpx.Timeout(None, connect=5.0)`・テストで固定済み）。この設計は
ローカル前提では正しかったが、**cloud モデル経由ではネットワークストールと
区別できない**。[[cooperative-deadlines-need-bounded-primitives]]:
協調的締切は全ブロッキング呼び出しの有限性が前提——1つの無限 I/O が全防御を無効化する。

## 設計

| 論点 | 決定 |
|---|---|
| read の既定 | **有限（600秒）**。実測の最長1呼び出しは 161.9s（qwen の思考爆発）で、約3.7倍の余裕。ollama は stream=False では生成完了までバイトが流れないため、read タイムアウト＝1生成の上限として効く |
| 注入 | `read_timeout` を `connect_timeout` と同格のコンストラクタ引数に。**呼び出し側が環境に応じて規定**（cloud 主体の probe は詰められる・特殊なローカル長生成は None も選べる）。既定は有限に倒す |
| リトライ | 追加実装なし——`httpx.ReadTimeout` は `TransportError` の子で、**既存の接続系リトライ梯子がそのまま受ける**（バックオフ→尽きたら Unreachable）。切ることが目的でなく、ストールからの回復が目的 |
| 旧テストの扱い | `test_default_client_has_connect_timeout_but_unbounded_read` は旧設計の意図的な固定。**設計転換として書き換える**（016→018 の ACL 格上げと同じ作法——当時の判断を消さず、覆した経緯をコメントに残す） |
| 検証 | **ストールの模擬**（接続を受けて応答しない実 TCP サーバ）に対し、有限時間で Unreachable に畳まれることを実測。正常系テストではこの穴は見えない（Skill の規範どおり） |

## 完了条件

- ストール模擬テスト: 応答しないサーバへの chat が**有限時間で** Unreachable になる
- 既定クライアントの read=600 / connect=5.0・`read_timeout` 注入（数値・None）のテスト
- ReadTimeout が既存リトライ梯子で吸収されることのテスト（一次ストールは回復）
- 全テスト green。以後の実走はすべて有限 read を継承（ハング再発時は別因を疑える）
