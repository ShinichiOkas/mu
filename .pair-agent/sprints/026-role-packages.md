# スプリント026 — 目的別ロールパッケージ 実装記録

- 期間: 2026-08-11
- 合意: [026](../agreements/026-role-packages.md)（師匠「OK。進めてください」）
- コミット: `3749053`（A 移動＋器）`a1edba9`（B 切替面＋coding 回帰）`8a19d04`（C research 初版）＋ D（実走ループ・本コミット）
- テスト: **320 green**（313→320。新規7件・機構は全フェーズ TDD）
- 実走: [runs/2026-08-11-026](../../runs/2026-08-11-026/README.md) — coding 回帰1走＋research 4走・全 achieved・violations none

## 主題 — 師匠の指示「目的別ロールパッケージを作成してこれらを切り替えて専門エージェントとして機能させる」

| フェーズ | 対処 |
|---|---|
| A 移動＋器 | roles/*.md → `roles/coding/`（自己完結パッケージ）。`manifest.json`（name / description / status）と `list_packages`（壊れたマニフェストは名指しエラー）。既定パスを roles/coding に変更 |
| B 切替面 | `MU_ROLES_DIR`（カンマ区切り合成可）を4入口すべてに配線。`show_roles` がパッケージの素性（名前・検証状態）を表示——verified 以外で走っていることが人間に見える。planned 枠3件（rnd / secretary / book） |
| C research 初版 | coding コピー＋researcher。**記録済みの失敗が種**: 020 の量化子弱化→pdm に PRESERVE QUANTIFIERS・qa に量化子照合、012 の言語 NG→researcher に「目的と同じ言語」 |
| D 実走ループ | runtime 課題（020 と同一）で 観測→調整→再走 ×4。r1: 人選誤誘導（implementer が本命執筆・予告どおり）＋単一ソース→pjm/researcher 修正。r2: 修正2件とも機能（researcher 執筆・公式ドキュメント7本）。転記エラー観測→修正。r3: 転記再発なし・未取得 URL 引用を観測→修正。r4: 未取得引用消滅・ただし単一ソース収束が再発（規範文では量を保証できない——構造対処は「深さの仕様化」へ） |

## 前置宣言した判断（5件＋実行中の調整2件）

レイアウト roles/&lt;package&gt;/／マニフェストは manifest.json（verified 昇格は師匠の承認事項）／切替は env（協議時 MU_ROLES→既存の MU_ROLES_DIR に調整・合意に追記済み）／研究のドメイン役割は researcher 1本から／pjm 人選指針は初回走行まで据え置き→r1 で誤誘導を実観測して修正（宣言どおりの順序）。

## 結果と残課題

- **切り替えは機能**: coding（verified）と research（draft）を MU_ROLES_DIR で切り替え、両方で実走達成。coding 回帰も期待どおり（bugfix 87s・ハッシュ一致）。
- **research は draft のまま**（昇格は師匠の判断。r4 の単一ソース収束から時期尚早）。
- 残課題は LONGTERM_TODO へ: リサーチの深さの仕様化（量の操作化・QA の出典照合）／probe_research の役割ロードが chdir 後（相対 MU_ROLES_DIR の入口間非対称）。
- 振り返り: 未実施（師匠に打診中）。
