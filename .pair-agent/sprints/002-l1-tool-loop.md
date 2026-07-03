# スプリント 002 — l1-tool-loop（完了）

- **期間**: 2026-07-03
- **ゴール**: L1（ツールコールのループ）を可能な限りシンプルに実装する
- **結果**: 達成。

## 成果

- **L1（`mu/l1.py`）** — 無状態 `step()`／`(func, usage_text)` ペア登録／system 注入＋構造化 tools。中断・再開は上位が messages を持つことで実現。
- **ツール呼び出しの確実化** — system prompt 強化。
- **検証用ツール `tools.py`** — read_file / write_file / edit_file / list_dir / execute_command（PowerShell）。
- **実タスク失敗の診断と改善** — 環境グラウンディング＝呼び出し側の責務（C）、暴走対策＝L2 の役割（D）。
- **テスト 34 green**（L0:16 / L1:9 / tools:9）。`l1_chat.py` に `tools.TOOLS` ＋環境プリアンブル。

## 振り返り（2026-07-03）

- vision: `~/.claude/pair-agent/vision/mu-002-l1-tool-loop.md`
- 新規 Skill: `test-with-real-ambitious-tasks` / `minimal-is-effective-not-fewest`（ペア固有）、`environment-grounding-is-caller-concern`（プロジェクト）
- 主な学び: 実タスクで叩くと統合・文脈の穴が出る／ミニマルは"効く最少"／**予見できた失敗点は先に規定すべき**。

## 次スプリント候補

- **003: L2（PDCA が明示的に乗る層）** — mu の核心「自立実行」に踏み込む。
