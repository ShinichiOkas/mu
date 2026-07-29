# pi との比較から学ぶ — 2026-07-30

隣接リポジトリ `../pi`（[earendil-works/pi](https://github.com/badlogic/pi-mono) — Mario Zechner らによる agent harness、TypeScript monorepo）が mu と非常に近いコンセプトを持つため、実装を調査し mu の観点で比較した。
調査は pi の 3 パッケージ（`packages/ai` / `packages/agent` / `packages/coding-agent`）を対象に実施。本文中の行数・ファイル名は 2026-07-30 時点の実物に基づく。

---

## 1. 概要 — 何が似ていて、何が違うか

| | mu | pi |
|---|---|---|
| 一言で | 自律性の層を内側から育てる汎用エージェント | 自己拡張可能なコーディングエージェント harness |
| 言語 / 規模 | Python **868 行**（L0〜L3 + tools） | TypeScript **約 108k 行**（monorepo、うち生成カタログ約 19k） |
| 依存 | `ollama` + `httpx` の 2 つ | pi-ai だけで 11（4 ベンダー SDK は遅延 import） |
| LLM | Ollama 専用（ローカル） | 35 プロバイダ / 9 wire protocol / 1,019 モデル |
| 中核思想 | **層**: 自律性を一枚ずつ外へ重ねる（L0→L4…） | **拡張**: core は最小、自律性は extension で足す |
| ゴール判定 | L2 Reflect / L3 overall が明示的に判定 | **core に判定層が無い**（モデルの自己申告で停止） |
| HITL | L3 の `approve` スロット（core 内） | `tool_call` hook の `{block, reason}`（extension が実装） |
| 状態 | 無状態。messages は呼び出し側が保持 | 3 段構え（純関数 loop → Agent → セッション永続 Harness） |

**思想の一致は本物**。pi の CONTRIBUTING.md は「pi's core is minimal. If your feature does not belong in the core, it should be an extension. PRs that bloat the core will likely be rejected」と明言しており、mu の三原則（シンプル・ミニマル・本質的）と同じ側に立つ。ただし「最小 core の外側に何を置くか」の答えが正反対で、mu は**層（構造）**、pi は**フック（拡張点）**で答えている。

### 層の対応マップ

| mu | 行数 | pi 側の対応物 | 行数 |
|---|---|---|---|
| L0（理想化された LLM） | 203 | `packages/ai`（正規化 transport。**理想化はしない**） | 35.5k |
| L1（ツールコールのループ） | 127 | `packages/agent/src/agent-loop.ts`（純関数の loop） | 748 |
| L2（Reflect / PDCA） | 165 | **対応物なし**。近いのは compaction の構造化サマリのみ | — |
| L3（大域 Plan + HITL） | 251 | **core に無い**。`examples/extensions/plan-mode`（約300行の拡張例）と実験的 `packages/orchestrator` | — |
| tools.py（検証用5ツール） | 94 | `coding-agent/src/core/tools/`（read/bash/edit/write ほか） | 約2.5k |

つまり mu が核心と考える L2/L3（判定と計画）を、pi は core に持たない。逆に pi が厚く作り込んでいる領域（截断・セッション・compaction・イベント・引数検証）は mu がまだ薄い。**両者の厚みは綺麗に相補的**であり、学びの多くは「pi が運用で踏んだ穴の埋め方」にある。

---

## 2. 学び A — mu の既知課題に直接効くもの（LONGTERM_TODO 対応）

### A-1. ツール引数の検証エラーを「修正可能な steering」にする
**対応する mu の課題**: LONGTERM_TODO「必須引数欠けエラーの steering」（F1-g/g2 で `write_file` の path 欠けが十数回連続、実時間の最大の浪費源）。

pi はツール引数を TypeBox スキーマで検証し、失敗時は**パスごとのエラー ＋ 受け取った引数のエコーバック**を error 結果としてモデルに返す（`packages/ai/src/utils/validation.ts`）:

```
Validation failed for tool "X":
  - /path: <message>
Received arguments:
{ ...json... }
```

「何が悪いか」と「自分が何を送ったか」を両方見せるので、モデルは次の周で自己修正できる。mu の `_invoke` は未知 kwarg を落とす防御（[l1.py:101](../mu/l1.py#L101)）は既に持つが、**必須引数欠けは素の TypeError 文字列**が返るだけで、usage_text の再提示も引数のエコーもない。ここに usage_text ＋ 受領引数を添えるだけで F1 最大の浪費源が塞がる見込み。mu の設計（幻覚 kwarg を落として注記する＝実行の頑健化）と同じ思想の延長で入る。

### A-2. 截断ポリシーと「続きの取り方」ヒント
**対応する mu の課題**: 「証拠デッドロック」（`read_file` 4000字截断 × transcript 6000字上限で、大きいファイルの全文提示が原理的に不可能）。

pi の截断は全ツール統一ポリシー（`coding-agent/src/core/tools/truncate.ts`、行数上限と byte 上限の併用）で、かつ**截断したら必ず「続きの取り方」を出力に書く**: 「continue with offset N」、bash は全出力を一時ファイルに退避してそのパスをモデルに伝える。截断が行き止まり（デッドロック）にならず、常に次の一手に変換される。

mu への示唆は 2 つ:
1. `read_file` の截断メッセージに offset 指定での続読手段を添える（ツール側の1行変更で入る）
2. より本質的には、LONGTERM_TODO が既に書いている「Reflect を実行ベースの証拠へ誘導する（機械可読な合格出力を criterion に要求）」方向が正しい。pi は「巨大な内容を transcript に載せる」のを最初から諦め、**実体はファイルに置きパスで参照する**。これは mu のファイル・グラウンディングそのものであり、証拠もファイル・グラウンディングに乗せるのが筋が良い。

### A-3. 判定を「表象」でなく「実体」に寄せる — tool result の構造化
**対応する mu の課題**: 偽・完遂 4 件の統一診断「判定が実体でなく表象に対して行われている」（合意005）。

pi のツール結果は `content`（モデル向けテキスト）と別に `isError: boolean` と型付き `details`（機械可読な事実。例: edit の diff、書き込んだバイト数）を持つ。つまり **「ツールが実際に何をしたか」が散文と別のチャネルで残る**。

mu の L2 Reflect が「transcript 上の提案コード」を証拠に採用してディスクを見ずに pass した事故（F1-g2 走行2）は、Reflect の入力が散文 transcript だけであることに起因する。ツール結果に最小限の構造化事実（成功/失敗フラグ、書き込みパスとバイト数など）を持たせ、Reflect にはそれを優先的に見せる — これは「表象への判定」を「実体への判定」に一段近づける、合意005 の方向と整合する具体策。

---

## 3. 学び B — 設計面で借りる価値のあるパターン

### B-1. compaction = 構造化チェックポイント
**対応する mu の課題**: 「長文脈でツール引数の忠実度が落ちる仮説」（F1-g2: 周を重ねると path 欠けが連続、messages リセット後は 8355 字を一発成功）。

pi はコンテキストが `contextWindow - reserveTokens` を超えたら自動で履歴前半を LLM 要約し差し替える（`coding-agent/src/core/compaction/compaction.ts`、893行）。注目すべきは要約テンプレートが固定の構造化フォーマットであること:

```
## Goal / ## Constraints & Preferences
## Progress (### Done / ### In Progress / ### Blocked)
## Key Decisions / ## Next Steps / ## Critical Context
```

これは実質 **PDCA のチェックポイント**であり、mu の語彙とそのまま噛み合う。mu は現状 compaction を持たず、L3 が単位ごとに L2 の messages を新規に張り直すことが事実上の対策になっている（F1-g2 の観測はこの効果を裏づける）。フル機構（893行）を移植する必要はないが、「**長くなった messages を Goal/Done/Next の構造化サマリに畳んで張り直す**」という 1 操作は、L2 の周回が伸びたときの防御としてミニマルに入り得る。切る位置は「turn 境界のみ、tool result の途中では切らない」という pi の規律ごと借りるのが安全。

### B-2. セッション = append-only の記録 + 導出される状態
**対応する mu の課題**: LONGTERM_TODO 低優先「L3 の中断・再開の対称性」（L4 着手時に検討と規定）。

pi のセッションは JSONL への **append-only ツリー**（各エントリが `id`/`parentId` を持つ）で、会話状態は「leaf から root へ辿って再生する」ことで**毎回導出**する（`packages/agent/src/harness/session/session.ts`）。書き換えない・消さない・現在位置の移動すら 1 エントリとして追記する。

mu は「状態は messages、上位が持つ」という無状態原則を既に持つが、永続化はまだ無い。L3 に中断・再開を足す段になったら、「L3 の内部状態（units/done）を可変オブジェクトとして保存する」のではなく「**イベント（plan / unit_done / replan…）を追記し、状態は再生で導出する**」形が、mu の無状態原則と最も整合する。なお mu の L3 は既に `log(event)` でイベントをタプルとして外へ出しており（[l3.py:107](../mu/l3.py#L107)）、このイベント列をそのまま永続化フォーマットに昇格できる素地がある。

### B-3. steering の一般化 — 3 種のキューと turn 境界規律
pi のループは介入を 3 つに区別する: **steer**（今の turn の直後に注入）/ **followUp**(停止しようとした時だけ注入) / **nextTurn**（アイドル時に積む）。いずれも注入は turn 境界のみで、ツール実行の途中には決して入らない。

mu は既に同じ規律を持つ（L1 docstring「周と周の境目で起きる」、L2 の `[L2] ` フィードバック再投入は steer と同型）。学びは新機構ではなく **概念の名前と区別**: L2 の再投入は「steer」、L4 が構想する「人間がいつでも介入できる」は「followUp/nextTurn」に相当し、pi の 3 分類は L4 設計時の語彙として使える。

### B-4. 承認ゲートの単一プリミティブ — `tool_call` → `{block, reason}`
pi のあらゆる承認ゲート（permission-gate、破壊的コマンド確認、保護パス）は、たった 1 つのフック「ツール実行前に `{block: true, reason}` を返せる」の上に extension として実装されている。core が持つのは判断の**差し込み口**だけで、判断そのものは外にある。

これは mu の「判断は外へ、実行は内で」（L3 の `approve` スロット）と同じ結論に別ルートで到達したもの。相互裏づけとして強い。さらに pi の plan-mode 拡張は「承認」を**能力制限**でも表現する（読み取り専用ツールセットに切り替える）。L4 の HITL 設計で「聞く」以外に「できることを絞る」という選択肢があることは覚えておく価値がある。

### B-5. ツールがプロンプト断片を持ち運ぶ
pi の各ツールは `description`（スキーマ用）とは別に `promptSnippet`（system prompt の一覧行）と `promptGuidelines`（そのツールが有効な時だけ system prompt に足される注意書き）を持つ。**プロンプトの断片がツールに同梱され、有効なツール構成から system prompt が自動組成される**。

mu の `(func, usage_text)` ペア（[l1.py:26](../mu/l1.py#L26)）は既にこの思想の最小形。pi との差分は「ガイドライン（使い方の注意）も同梱し、構成に応じて注入が変わる」点だけで、usage_text を `(一覧行, 注意書き)` に割る拡張は自然に接続する。急ぐ必要はないが、方向の正しさの裏づけになる。

### B-6. 失敗してもイベント列を壊さない
pi は LLM 呼び出しが失敗しても例外を伝播させず、`stopReason: "error"` の**合成 assistant メッセージ**を作って通常のイベント列（message_end → turn_end → agent_end）を最後まで流す。観測者は「途切れた列」を見ることがない。また履歴再送時には、孤児になった tool_call に「No result provided」の tool result を合成し、**messages が常に整形式であることを不変条件として守る**（`transform-messages.ts`）。

mu は L0 の 4 型エラーが例外として上がる設計で、これ自体は正しい（後述 4-1）。学びは「messages の整形式性は誰かが保証する必要がある」という点で、L1 が中断された場合などに tool_call と tool result の対応が崩れた messages を再開時にどう扱うか、L3 の中断・再開を設計する際の論点として持っておく。

---

## 4. 学び C — 比較して確認できた mu の強み（変えないほうがよいもの）

### C-1. 型付き 4 エラーは pi の弱点の正解
pi-ai のエラー面は `stopReason`（5値）＋ **自由テキストの errorMessage** だけで、リトライ判定は約 55 個の正規表現（`retry.ts` 約30 + `overflow.ts` 23）を手で足し続けている。コメントには issue 番号（#1123, #2264, #3317…）が並び、穴が開くたびにパターンを足した痕跡そのもの。mu の「生エラーを隠して 4 型に畳む」は、この泥沼を構造で回避しており、**維持すべき明確な優位**。

同時に、pi-ai のリトライは既定 0 回で「方針は上位が持つ」という割り切りであり、mu の「L0 がリトライまで畳み込む」とは責務の切り方が逆。mu は単一プロバイダ（Ollama）だから畳み込みが成立している。マルチプロバイダ化するなら pi 型の分離が要る — 逆に言えば、**Ollama 専用を保つ限り mu の畳み込みが正しい**。

### C-2. 構造化出力は mu にあって pi に無い
意外な発見だが、pi-ai に構造化出力（response_format / JSON schema）は**存在しない**。pi で構造を得る唯一の道は「ツールを 1 つ定義して引数を読む」。mu の L2 Reflect / L3 の生命線（verdict / plan / analysis）は Ollama の `format=schema` に全面的に依存しており、これは Ollama 専用構成の恩恵。**mu の判定アーキテクチャは、pi のスタックの上では同じ形で作れない**。L0 の抽象を広げる議論が将来出た場合、構造化出力が boundary になることを覚えておく。

### C-3. 明示的な検証層そのものが mu の独自性
pi のループは「モデルが tool_call を出さなくなったら終わり」— 完遂の検証は無い。mu が F1 で苦しんでいる偽・完遂は、**検証しようとしているから見えている問題**であり、pi はそもそも検証しない（ユーザーが対話で見ているから成立する）。mu は自走（人間の逐次介入なし）を目標とするので、この差は本質的。pi から検証層の答えは得られない — 合意005（L4）は自力で進むしかない領域だと確認できた。

### C-4. 上限は呼び出し側が規定する、という規律
pi のループには max_rounds に相当するものが**無い**（steering/followUp が空で tool_call が止まれば終わる）。対話型ではそれで成立するが、自走では停止保証がない。mu の「上限は呼び出し側が規定」（L1/L2/L3 一貫）は自走前提の設計として正しく、維持する。

---

## 5. 規模感の教訓 — 「同じ最小思想」の 10 年後の姿

pi も「core は最小」を掲げるが、実運用の要請（35 プロバイダ、截断、セッション、compaction、TUI、拡張機構）を吸った結果、monorepo は約 108k 行に達している。それでも**純関数のループ本体は 748 行**に保たれ、周辺機能は層（Agent → Harness）と拡張に押し出されている。

mu にとっての教訓は二つ:

1. **核を薄く保つ戦い方は「層 or 拡張への押し出し」**。pi は最小 core を守るために Harness という「第 2 の厚い層」を作った。mu の 1 層 = 1 ファイル規約は同じ圧力への別の答えであり、「1 ファイルに収まらない＝責務を見直すシグナル」はこの比較でも有効に見える。
2. **運用で必ず生える機能の一覧が先に見える**。截断ヒント・引数検証・compaction・セッション永続は、pi が数千 commit かけて「無いと困る」と学んだもの。mu は F1 実走でそのうち 2 つ（截断・引数検証）に既に自力でぶつかっている。残り（compaction・永続化）も自走時間が伸びれば来る、という予告として読める。

---

## 6. まとめ — 優先順の提案

mu の現在地（クールダウン中、L4 協議中、LONGTERM_TODO 残あり）に照らした優先順:

| 優先 | 項目 | 効く先 | 重さ |
|---|---|---|---|
| 1 | A-1 引数検証エラーの steering（usage_text＋受領引数のエコー） | LONGTERM_TODO 既存項目 | 小（`_invoke` の数行） |
| 2 | A-2 截断に「続きの取り方」を添える | 証拠デッドロック | 小（tools.py） |
| 3 | A-3 tool result に構造化事実（isError 等）を持たせ Reflect に見せる | 偽・完遂（合意005 の具体策） | 中。L4 協議と一体で検討 |
| 4 | B-1 構造化チェックポイント（Goal/Done/Next への畳み込み） | 長文脈仮説 | 中。仮説の切り分け実験が先 |
| 5 | B-2 イベント追記型の永続化 | L3 中断・再開（L4 着手時と規定済み） | 中。設計方針のメモとして保持 |

1・2 は LONGTERM_TODO に既にある項目の**実装方針が pi の実物で裏づけられた**という位置づけ。3 は合意005 の「表象→実体」診断への具体策なので、L4 スプリントの協議材料に入れるのが良い。4・5 は急がない。

なお C 節（4 型エラー・構造化出力・検証層・上限規律）は「pi を見た結果、変えない理由が強化された」項目であり、対処不要。

---

*調査メモ: pi 側の参照は `packages/ai`（35,545 行 / 147 ファイル）、`packages/agent`（8,055 行 / 25 ファイル、うち loop 本体 748 行）、`packages/coding-agent`（51,122 行 / 170 ファイル）。主要ファイル: `agent-loop.ts` / `agent-harness.ts` / `compaction.ts` / `truncate.ts` / `validation.ts` / `transform-messages.ts` / `retry.ts` / `overflow.ts`。*
