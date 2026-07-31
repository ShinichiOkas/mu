# スプリント006 — PjM プロセス（役割注釈付きタスク列）実装記録

- 期間: 2026-08-01（協議〜完了が1日）
- 合意: [../agreements/006-pjm-role-process.md](../agreements/006-pjm-role-process.md)
- 実験記録: [../../docs/experiment-2026-08-01-l4-pjm.md](../../docs/experiment-2026-08-01-l4-pjm.md)
- ビジョン記録: `~/.claude/pair-agent/vision/006-pjm-role-process.md`

## 成果

- roles/（PjM のナレッジベース: architect / implementer / qa 定義書）
- L4 = PdM(specify) + PjM(プロセス生成・人選・部分再実行判断 rerun/replan/respec/escalate)
- 実行はコードの逐次ループ: 役割定義を system 前置した L3 に1タスクずつ委任（L3 無変更）
- QA タスク化（verdict.md 機械読み、assess 廃止、QA 欠落はコード補完）
- 部分再実行: 選択的無効化＋ファイル依存伝播＋QA 必再実行（コード側）
- 入力保護 `tools.protect()`（解除条件発火による機構化）
- テスト 111 → 115 green — 1cab20f〜c758356

## 受入検証（実機 8 走）

偽・完遂 0/8。achieved 5（F1×31b 10分・sales×31b 137秒・F1×12b・sales×12b保護あり 等）、
正直な escalate 3。F1・sales ともプロジェクト史上初の本物の完遂。
部分再実行フルサイクル（respec→rerun→rerun、rounds=3）を実機観測。
穴探査走（12b）が3穴を発見: PjM staffing ミス（→プロンプト指針）、QA の自己修正→自己承認
（→役割別ツール制限を協議事項に）、入力を作り直すプロセス経由の破壊（→tools.protect 実装）。

## 学び（Skill 化済み）

- [[roles-are-task-data-not-code-structure]]（confirmed・新規）
- [[role-discipline-needs-permission-guards]]（forming・新規。ツール制限実装で昇格予定）
- [[defer-with-release-condition]]（confirmed へ昇格・mu 2連続実証を追記）
- [[verification-models-by-role]]（精緻化: 穴探査走の価値）

## 持ち越し

- **並列実行**（合意006 が明示的に後続へ送った本丸。依存グラフは部分再実行と共用で敷設済み）
- QA の役割別ツール制限（ガードレール。師匠も必要性を示唆）
- PdM への入力実物グラウンディング（specify が形式を発明する問題）
- シェルリダイレクト経由の入力保護の残穴
