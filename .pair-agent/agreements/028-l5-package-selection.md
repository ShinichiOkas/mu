# 合意 028 — L5 によるパッケージ自動選択の内在化

status: completed（2026-08-12。3フェーズ完了・330 green・選択精度 18/18・e2e 収束・スモーク合格・振り返り実施済み）
created: 2026-08-11

## 背景

vision/024 で記録した方針の実装: パッケージ選択は現在 L6（人間・呼び出し側）の判断であり、
内在化するなら座席は L5（目的粒度の判断・Director）。実装時の規律も記録済み——
**カタログは呼び出し側が規定・選択は構造化出力の1判断・適合セットが無ければ escalate**
（小説の目的に coding セットを黙って当てない）。027 完了で5パッケージが揃い、
着手条件（検証済みセット2つ以上）を満たした。師匠の選択（2026-08-11）。

## 設計（師匠承認 2026-08-12「OK.良い方針です」）

- `Director.run(packages=...)`: カタログ＝ `list_packages()` の出力そのもの。
  **roles= 明示（L6 手動）が常に優先**。roles 無し＋packages 有りのときだけ、
  specify の前に選択の1判断（構造化出力 `{package, reason}`）→ 選択パッケージを load。
  結果契約に `package` 欄を追加（選択の正しさを機械検査可能に）。
- **決定論の床（escalate 3経路）**: ①適合なし申告 ②カタログに無い名前 ③選択先が
  planned／役割文ゼロ——いずれも黙って別パッケージを当てず escalate。
- **選択の「やり方」は `roles/director.md`**（カタログ級・パッケージ横断の定義書。
  コードが名前を知る5つ目の名前だが人選対象ではなく、4ポジション契約は不変）。
  無ければ知識ゼロで判断（既存哲学・`role_doc_missing` で可視化）。
  選択の材料は manifest の description（データ）。
- **表面は `MU_ROLES_DIR=auto`**（opt-in。既定は従来どおり coding——既定を変えない）。

## スコープ（フェーズ＝コミット単位）

1. **A — 機構（TDD）**: `Director.run(packages=, selector=)`・選択判断・escalate 3経路・
   結果契約 `package` 欄。ユニットは FakeL0 で全経路（選択成功／手動優先／適合なし／
   未知名／空パッケージ）。
2. **B — 表面＋director.md**: `MU_ROLES_DIR=auto`（chat_common にカタログのロードと表示、
   probe_hard / l5_chat / l4_chat / probe_research へ配線）・`roles/director.md` 初版
   （職掌レベル＋vision/024 の規律）・README 明文化。
3. **C — 実証実験＋クローズ**: (1) 選択のみの精度: 6目的（5ドメイン既知課題＋適合なし
   1件）×3反復 live 計測→失敗観測があれば director.md 調整→再測 (2) e2e 2本:
   auto で schedule（期待: secretary）と book（期待: book）を完走 (3) coding スモーク
   （confirmed スキル [[smoke-test-before-close-after-prompt-changes]]）＋runs/ 記録。

## 実行中に採る判断（AI の判断。事後確認対象）

- 選択の LLM 呼び出しは既存の `lifeline_system` 機構を流用（`{"director": doc}` を渡す）。
  定義書不足の可視化・スキーマ供給が既存の床に乗る。
- 表面（auto モード）が渡す既定カタログは **planned を除外**（役割文ゼロは選ばせない。
  床③の手前の親切。カタログは呼び出し側規定なので上書き可能）。
- 選択の実況イベント `("package", name, reason)` を log 契約に追加（chat_common が表示）。
- director.md の初版は職掌＋記録済み規律（無理に合わせない・同等適合なら verified 優先）
  のみ——選択品質の規範文は C の失敗観測から（スキル準拠）。
- 実験条件は 021〜027 と同一（gemma4:31b-cloud＋qwen3.5:9b・MU_TIME_BUDGET=1500）。

## 完了条件

- roles 無し＋packages 有りで選択→load→完走が通り、escalate 3経路が床として機能（テスト）
- `MU_ROLES_DIR=auto` の e2e で正しいパッケージが自選され課題達成（schedule→secretary・book→book）
- 選択のみ精度の計測記録（適合なしの正直さ含む）が runs/ にある
- coding スモーク合格・テスト全 green・README 明文化

## やらないこと（スコープ外）

- 複数パッケージの自動合成・選択の学習・verified 昇格・既定モードの変更（auto を既定にしない）
