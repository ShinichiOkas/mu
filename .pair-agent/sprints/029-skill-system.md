# スプリント029 — skill システムの導入（役割定義書からの知識の分離） 実装記録

- 期間: 2026-08-12（相談〜協議〜合意〜3フェーズ実装〜実証〜振り返りが1日）
- 合意: [../agreements/029-skill-system.md](../agreements/029-skill-system.md)
- 実走記録: [../../runs/2026-08-12-029/README.md](../../runs/2026-08-12-029/README.md)
- ビジョン記録: `~/.claude/pair-agent/vision/029-skill-system.md`
- コミット: `4613bfc`（A 機構）/ `1eb5406`（B 移行・表面）/ `77b7916`（C 実証）

## 発端（師匠の相談）

> Mu には SKILL の概念が無いが、role の概念は SKILL の上位概念の様にも捉えられる。
> ……どのレイヤーにすべきか、また role との関係をどうするべきかが重要になる。

## 中心にあった把握（振り返りで師匠が言語化）

既存の SKILL システムは**役割の概念を持たず、やることに直接バインド**する。
mu は L4 の人選で「やること → やる人」を既に持っていた。そこへ skill を足したことで
**やること → やる人 → やり方**の連鎖が閉じた。「role は skill の上位概念」は
**包含ではなく連鎖の上流**の意味であり、だから宛先を skill 側に名乗らせる設計が自然に落ちる
——やり方は**やる人を経由して**タスクに届く。

## 設計（3点が師匠確定）

1. **skill は層ではない。** 層は判断を足すが skill は知識を足す。よって層の外のデータ
   （`skills/*.md`）＋ facility（`mu/skill_kb.py`）で、装着点は既存の合成点。
2. **宛先は skill の側が名乗る**（`applies_to`。一方向）。②（プロジェクト方針）は
   共有資産を書き換えられず、028 の自動選択下では役割名も確定しないため。
   確実に名指しできるのは名前が動かない4ポジションだけ。`all` は明示形も省略も同義で、
   表示は常に `all` に正規化。
3. **skill は権限を持たない（絶対ルール・師匠宣言）。** `tools:` / `write_scope:` は
   パーサが名指しでエラーにする（静かに無視しない）。

加えて **`maturity: confirmed` だけが装着される**門を置いた（③への接続点。系が書けるのは
draft まで・確定は人間＝026 と同型の非対称）。未知の frontmatter キーは持ち回るので、
素性（出所・根拠の実走）は契約を変えずに後から載せられる。

## 成果

- **`mu/skill_kb.py`**（新 facility・`role_kb.py` の隣）: `load_skills` / `parse_skill_doc` /
  `attached_skills` / `skill_text` / `unknown_targets` / `equipment_lines`。
  意味論は roles に揃えた（セット合成・同名衝突は両出所を名指しするエラー・欠損は空集合）
- **装着**: `task_system` は `職掌 → 装備 → 契約 → 環境`。ポジション（pdm/pjm/director）は
  `lifeline_system` でも着る。**skills 省略時の合成は 029 以前と1文字も変わらない**（テストで固定）
- **移行**: `roles/*/implementer.md`（5パッケージ・バイト同一の27行）→ 9行。抜いた6件は
  `skills/` へ。**役割定義書への追記はゼロ＝削除のみ**
- **表面**: `MU_SKILLS_DIR`（既定＝同梱 `skills/`・カンマ区切り合成可）・起動表示
  `show_skills`（出所・装備の逆引き・宛先不一致の名指し・skill ゼロの明示）
- テスト 330 → **364 green**

## 実証（runs/2026-08-12-029）

| 検証 | 結果 |
|---|---|
| 移行の文言不変 | 行の多重集合が**完全一致**（消えた行 0・増えた行 0）。差は空行 +5 字と並び順のみ |
| 回帰スモーク（bugfix） | **achieved 105s**（028 の同課題 198s）・保護入力ハッシュ一致・テスト実体 9件 OK・violations none |
| ②の e2e | プロジェクト側 skill 1本で実装者のやり方が変わり（成果物1行目に案件マーカー）達成はそのまま。共有ライブラリ・役割定義書は無変更 |

## 前提崩壊 1回

「装着点は L4 の1行」が誤りだった。装着点を確定させていたのは**承認済みの `applies_to` の
語彙**（4ポジション）のほうで、pdm/pjm は別経路（生命線）に居る。コード側から数えたので
足りなかった——語彙の側から数えるべきだった。実装中に気付いて回収。
→ [[count-registration-points-not-the-checklist]] に断面を追記。

## 学び（Skill 化済み）

- [[knowledge-containers-must-not-carry-permissions]]（domain・**confirmed**・師匠の明示宣言。
  ※協議中に即時登録すべきだったのを振り返りで回収）
- [[extension-declares-its-own-target]]（domain・draft・新規）
- [[prompt-migration-proved-by-line-multiset]]（process・draft・新規）
- [[role-structure-by-design-norms-by-failure]]（forming → **confirmed 昇格**。029 が第2標本
  ——役割以外の構造でも「構成は設計から／規範文は失敗から」が成立）
- [[count-registration-points-not-the-checklist]]（confirmed・精緻化: 語彙の側から数える）

## 開いた問い（次の協議の種・師匠が閉じずに残した）

> 自己成長するためには成長目標が無いといけないが、Agent としてのレイヤーを積む行為と
> 成長目標がかみ合うか？ レイヤーなのか？

論点: 029 で「知識を足すものは層ではない」と確定したが、**成長**は判断を足すのか別軸なのか。
成長目標は走を跨ぐので、持った時点で mu は無状態でなくなる（三原則「状態・記憶の少なさ」と
正面衝突）。029 が用意したのは maturity の門だけで、これは**成長の速度を人間が律速する**形
——③ の設計はこの律速を保つか外すかが分岐点になる。

## 残した宿題

- 装備が増えたときの context 影響は未測定（implementer で 865→1,073 字）
- `applies_to` にドメイン役割名を書いたときの可視化は実走未確認
- スコープ外のまま: (b) PjM による task ごとの skill 選択 ／ ③ の書き戻し機構 ／
  `qa.md`・`pdm.md` の共通部抽出（implementer で型が固まってから）
