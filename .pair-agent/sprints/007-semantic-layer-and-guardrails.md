# スプリント007 — 意味の層の穴とガードレール 実装記録

- 期間: 2026-08-02〜08-04（協議〜完了）
- 合意: [../agreements/007-semantic-layer-and-guardrails.md](../agreements/007-semantic-layer-and-guardrails.md)
- 実走記録: [../../runs/2026-08-02-007/README.md](../../runs/2026-08-02-007/README.md)
- ビジョン記録: `~/.claude/pair-agent/vision/007-semantic-layer-and-guardrails.md`

## 主題

**プロンプトで頼んでいる規律を、コード側の機構に落とす。** 006 の持ち越し（並列実行を除く3件）と
難課題 H1-H6 の新発見2件をまとめて処理した。並列実行は師匠の判断でスコープ外。

## 成果

- **C1 矛盾の独断解決**（三重）: specify/respecify に規範 ＋ `_SPECIFY_SCHEMA` の
  `feasible`/`conflicts` 申告 ＋ `feasible=false` なら PjM を起動せず即 escalate（コードの分岐）
  ＋ QA タスクに PURPOSE 原文を接地し `roles/qa.md` に必須検査項目を追加
- **C2 入力の実物への接地**: `_input_grounding()` が workdir の実在ファイル（一覧＋先頭抜粋）を
  specify / respecify に前置。「実物と食い違うならファイルが正」を規範に
- **B1 役割別ツール権限**（全役割へ一般化）: `roles/*.md` の frontmatter に宣言、`_role_tools` が適用。
  PjM は role 名しか出せないので権限を書き換えられない
- **B2 保護の意味論**: 「内容不変だけを守る／ディレクトリ不変は採らない」と明文化し、
  `protection_violations()` で破れを検出
- 冒頭の説明（l4.py / l4_chat.py / tools.py）と **README の L4 節**を実態に同期（師匠の指摘）
- テスト 115 → **140 green** — 9b078df〜2d79a2a

## 受入検証（実走）

| | 結果 |
|---|---|
| H3 contradiction ×3（同構成） | **3/3 escalate**、rounds=0・各1秒（前回は64秒で achieved＋0バイト shared.log） |
| 正常系4件（bugfix/jsonparse/deadstock/perf） | **すべて achieved、誤発火 0/4**。deadstock は正解 P007・P010 維持 |
| f1×12b（B1 の観測構成） | **`権限で拒否: (qa) write_file -> todo_app.py` が発火**。拒否後 QA は成果物を直さず検証を継続。走行自体は正直な escalate |
| 保護の破れ | 全走 none |

## 学び（Skill 化済み）

- [[guards-must-preserve-observability]]（process・confirmed・新規）
- [[norm-needs-a-declaration-slot]]（process・confirmed・新規）
- [[permissions-as-data-applied-by-code]]（process・confirmed・新規）
- [[mechanism-change-updates-layer-docs]]（feedback・confirmed・新規。師匠の指摘2回から）
- [[role-discipline-needs-permission-guards]]（forming → **confirmed**。実走で発火を確認）
- [[sprint-acceptance-is-the-observed-failure]]（精緻化: ガードの実証は弱い構成でしか行えない）

## 記録した思想（スプリント横断）

- `mu-autonomy-experiment-purpose` — 裏目的は「どこまで自立実行させられるか」の実験。ゴールは定めない
- `mu-division-of-labor-rationale` — 人間の分業＝専門性の限界、AI の分業＝スコープを狭めて確実にする。
  共通は並列化。構造は PMBOK 等を参照しつつ、AI 固有の分業ナレッジが溜まるはず
- `master-experience-derived-design` — 設計の出どころは長期の運用経験の翻訳

## 持ち越し

- **l4.py のミニマイズ**（827行。コアコードとロール定義・プロンプトの分離。師匠のビジョン。次の主要候補）
- **並列実行**（006 から継続。依存グラフは敷設済み）
- PjM が QA タスクを複数立てると本命の判定書が割れる（f1×12b で観測。LONGTERM_TODO）
- 証拠デッドロックの記述の見直し（`read_file` に offset が無い件。005 以降の構造で大半は解消済み）
- PMBOK 的な知識エリアで唯一空欄の**リスク**（失敗しうる点を先に宣言する機構）
