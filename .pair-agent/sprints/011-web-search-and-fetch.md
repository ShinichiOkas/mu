# スプリント011 — web 検索・取得ツールの追加 実装記録

- 期間: 2026-08-05（協議〜実装〜記録が同日）
- 合意: [../agreements/011-web-search-and-fetch.md](../agreements/011-web-search-and-fetch.md)
- ビジョン記録: `~/.claude/pair-agent/vision/011-web-search-and-fetch.md`
- コミット: `2ca30c7`（ツール追加）/ `c17cff4`（位置づけの明文化）

## このスプリントの目的（師匠の明示・実装後に語られた）

**汎用性の検証への準備**である。mu は汎用エージェントを名乗るが、ここまでの実装・検証は
事実上**コーディングエージェント**として積み上げてきた。web ツールは
「ディープリサーチのような**コーディング以外のタスク**」を走らせるための材料。

> muそのものは材料であり、mu/*を使って各種エージェントを作ることが目的。

## 成果

| ツール | 実体 |
|---|---|
| `web_search(query, limit=10)` | DuckDuckGo lite に POST → `html.parser` でタイトル/URL/抜粋を抽出。**API キー不要・依存追加なし**。DDG がリダイレクト URL を挟む場合は実 URL に戻す |
| `fetch_url(url)` | 取得して本文をテキスト化（script/style/nav 等を落とすだけ）。長い本文は全文を一時ファイルへ（010 と同じ規則）。続きは `read_file` |

- **失敗を正直に返す**のが設計の芯: HTTP 4xx/5xx は `ok=False` ＋ `facts.status`、
  検索 0 件も「無い」ではなく「取れなかったかもしれない」（レート制限・構造変化）として `ok=False`。
  空文字で成功を装わない
- `TOOLS` は 5 → 7。`roles/*.md` の `tools:` は**省略＝全許可**なので、
  **QA だけは明示リストにより自動的に除外**される（役割規律は roles を触らずに保たれた）
- 3層で実装（純粋整形＝固定サンプルで CI / I/O＝live マーカーで実ネット / 登録）。テスト 190 → **203 green**

## 検証

- 実物: `web_search("Ollama structured outputs")` → 3件取得 → 先頭 URL を `fetch_url` →
  4,495 文字（切り詰め）→ 全文 442 行を `read_file` で辿れた。`ja.wikipedia.org` は 403 を正直に返した
- L1 の dispatch 経由も確認: `limit="2"`（文字列）と幻覚引数 `max_results` の混入を吸収して実行
- **未検証**: モデルによる実走（弱いモデルが `web_search` → `fetch_url` と繋げられるか）。→ 012 で見る

## 協議の実績と、AI 側のズレ

選択肢は提示前に実測した（Brave は新規無料枠廃止済みのため除外、Tavily はキー要、
キーレス DDG はこの環境で現に動くことを確認してから提示）。

一方で **AI は「mu の依存が増える」を実在しないコストとして提示していた**。師匠の補正:
依存最小がかかるのは**コア（`mu/l0`〜`l5`）だけ**で、ツールが外部に依存するのは自明。
結論（キーレス）は変わらないが**理由が違っていた**——「依存を増やせないから」ではなく
「キー登録なしで今すぐ動き、検証に十分だから」。
→ Skill [[core-deps-minimal-tools-may-depend]] / [[material-not-the-finished-agent]]（ともに confirmed）、
README「mu は材料である」節、LONGTERM_TODO の検証項目に反映。
