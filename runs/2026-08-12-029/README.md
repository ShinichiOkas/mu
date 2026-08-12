# 029 実走記録 — skill システムの導入（2026-08-12）

合意 [029](../../.pair-agent/agreements/029-skill-system.md) フェーズ C の検証。
確かめたのは3つ——**移行で文言が変わっていないこと**・**移行が性能を落としていないこと**・
**プロジェクト側 skill（目的②）が実際に効くこと**。

実験条件は 021〜028 と同一: `gemma4:31b-cloud`（既定）＋ `qwen3.5:9b`（QA プール）・
`MU_TIME_BUDGET=1500`・課題は coding の `bugfix`（保護入力 `test_stats.py` を1文字も
変えずに `buggy_stats.py` を直す）。

## 1. 合成の検証 — 文言は1文字も変わっていない

`composition-diff.txt`（再現スクリプトは同ファイル冒頭の手順どおり）。

| | 移行前（`4613bfc`） | 移行後 |
|---|---|---|
| 出所 | `roles/coding/implementer.md`（27行） | 役割定義書（9行）＋ `skills/` の6件 |
| 行の多重集合 | — | **同一**（消えた行 0・増えた行 0） |
| 文字数 | 862 | 867（**+5 ＝ skill 間の空行のみ**） |
| 箇条書きの並び | 原文の順 | ファイル名順（**唯一の変化**） |

移行は「役割定義書から削って skill に移す」だけで、抜いた文面には手を入れていない。
順序だけが変わるので **no-op ではなく再測定**として扱い、下の 2 を回した。

## 2. 回帰スモーク — 性能低下なし

`bugfix-smoke.log` / `bugfix/`（既定の skill セットのみ＝移行分6件）。

| | 結果 |
|---|---|
| achieved / escalated | **true / false** |
| 所要 | **105s**（028 の同課題 198s） |
| 保護入力 `test_stats.py` | **ハッシュ一致**（`32ff7345870bb27f`。無傷） |
| テスト実体 | `python test_stats.py` → **Ran 9 tests / OK** |
| protection violations | none |

判定は verdict だけでなく**実体**（ハッシュ・テストの実行出力）で確認した。
偽・達成なし。所要が短いのは走ごとのばらつきの範囲で、少なくとも低下はしていない。

## 3. プロジェクト側 skill の e2e — 目的②が効く

`bugfix-project.log` / `bugfix-project/`。同一課題・同一条件に、プロジェクト側の
skill セットを1本足しただけの走:

```
MU_SKILLS_DIR=skills,runs/2026-08-12-029/project-skills
```

足した skill は [`project-skills/project-marker-comment.md`](project-skills/project-marker-comment.md)
——「この案件で作成・修正した Python ファイルの1行目に `# project: kaizen-2026` を置く。
**読むだけのファイル（入力・テスト）には足さない**」。`applies_to: implementer`。

| | 結果 |
|---|---|
| 起動表示 | `[skills] 出所: skills, runs/2026-08-12-029/project-skills` ／ implementer の装備 **7件**（共有6＋プロジェクト1） |
| achieved / escalated | **true / false** |
| 所要 | 73s |
| **成果物の1行目** | **`# project: kaizen-2026`** ← プロジェクト方針が効いた |
| 保護入力 | ハッシュ一致・**マーカー混入なし**（「読むだけのファイルには足さない」も守られた） |
| テスト実体 | Ran 9 tests / OK |
| protection violations | none |

**目的②が成立している**——共有ライブラリを書き換えず、役割定義書にも触れず、
`MU_SKILLS_DIR` にプロジェクトのセットを足すだけで、実装者のやり方が変わった。
役割パッケージ（coding）は手つかずのままである。

## 分かったこと

- 宛先を skill 側に置く設計は、実走で**そのまま機能した**。プロジェクト作者は
  `applies_to: implementer` と書くだけでよく、パッケージの中身を知る必要がない。
- 「読むだけのファイルには足さない」という**skill 内の但し書きが効いている**
  （保護入力にマーカーが付かなかった）。ただし標本1であり、規範文としての強さは未測定。
- 装備の逆引き表示が走の冒頭に出るので、「何を着て走ったか」が記録から後追いできる。

## 残した宿題

- 装備が増えたときの context 予算の影響は未測定。implementer の system は
  **職掌 129字＋装備 736字＝865字**（共有6件）／**＋プロジェクト1件で 1,073字**。
  劣化が出るとすれば装備が10件を超えたあたりのはずで、そこは観測が要る。
- `applies_to` にドメイン役割名を書いた場合の可視化（`unknown_targets`）は
  ユニットテストのみ。実走での確認は未実施。
