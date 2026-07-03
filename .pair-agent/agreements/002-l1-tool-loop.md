# 合意ドキュメント 002 — L1（ツールコールのループ）

- **sprint**: 002-l1-tool-loop
- **status**: active
- **開始**: 2026-07-03
- **前提**: L0 完成（Ollama インタフェースの理想化）

---

## ゴール

L1 = **ツールコールのループ**を、可能な限りシンプルに。L0 の上に、行動する層（Do）を1枚重ねる。

## ループの本質（確定）

```
chat を呼ぶ
  → 返答に tool_call あり → ツール実行 → 結果を付けて chat → ループ
  → 返答に tool_call なし → 終わり
```

## 決定事項

1. **無状態 step()**: `step(model, messages, tools) → (messages, done)`。1回の chat ＋ その tool_calls 実行で「**1周**」進める。`done` = その周で tool_call が無かった。`run()` は done まで step を回す薄いループ。
2. **状態は上位が持つ（＝messages）**: L1 に状態を残さない（ミニマル軸4）。**中断** = 上位が step を呼ぶのをやめる。**再開** = 保存した messages で step を呼ぶ。いずれも**周と周の境目**で起きる（ツール実行の途中では止めない）。
3. **ツール登録 = `(func, usage_text)` ペアのリスト**。L1 はこのリストから3つを導出:
   - **system prompt へ注入** ← 各 `usage_text` を束ねる（汎用化・弱いモデルへの誘導）
   - **`chat(tools=[func,...])`** ← 構造化スキーマ（`tool_calls` を確実に受け取る）。関数→スキーマは公式 `ollama._utils.convert_function_to_tool` が自動生成（名前・docstring・型ヒントから）
   - **dispatch** ← `{func.__name__: func}`（実行するのは mu 側）
4. **両輪**: ①テキスト（汎用化）＋②構造化（確実なパース）。v1 は tool_calls のパースを構造化に任せる。
5. **ツール実行の例外は結果として model に返す**（回復可能に）。未知のツール名も同様にエラー文字列を返す。

## v1 スコープ外 / 未決

- 完全モデル非依存（`tools=` を使わず system prompt テキストのみからツール呼びをパース）
- ストリーミング（L0 同様 v1 外）
- 1周に複数 tool_calls が来た場合の扱い（当面は順次実行）

## 進め方（確定ルール準拠）

- **1層=1ファイル** `mu/l1.py` ／ 内側から一層ずつ完成 ／ **`l1_chat.py`** を用意
- TDD・テスト通過で評価・実接続検証

## 実装メモ（L1 / 2026-07-03）

- コード: `mu/l1.py`（`ToolLoop`）。テスト: `tests/test_l1.py`（フェイク L0 で 8 件）＋ `tests/test_l1_live.py`（実接続 1 件）。**全体 25 green**。
- CLI: `l1_chat.py`（例ツール add / multiply / now、step 駆動でツール実行を表示）。既定 `qwen3.5:4b`。
- メッセージ構造は実物で裏取り（`Message`: role/content/tool_name/tool_calls、`arguments` は dict）。
- **確実化（2026-07-03 解決）**: 小型モデルは曖昧・和文プロンプトだとツールを呼ばず直答することがあった（例「23 かける 47」を割り算と誤読）。→ system prompt ヘッダを強化（"...you MUST call the appropriate tool instead of answering from memory..."）。同じ和文プロンプトでツールを呼び正答することを実機確認。
- **検証用ツール**: `tools.py` に `read_file` / `write_file` / `edit_file` / `list_dir` / `execute_command` を `(func, usage_text)` ペアで用意。`tools.TOOLS` をそのまま L1 に渡せる。

## 実タスク検証と改善（2026-07-03）

- 師匠が `l1_chat` で「フォルダを読んで要約 → abstract.md」を試行 → 大量エラーで問題露呈（本人談: お題が無謀）。
- **診断**: ① `execute_command` が utf-8 固定で cmd 出力(cp932)を文字化け ② エージェントに環境の地面（OS/shell/cwd/ファイル一覧）が無く、Unix コマンドを仮定・パスを幻覚 ③ ツール失敗時の暴走 ④ shell 不一致。
- **切り分け**: L1 のループは正しく動作していた（間違ったツールコールも忠実に実行）。壊れていたのは**ループではなくツールと文脈**。環境の文脈は L1 の責務ではなく外側が与えるもの、と確認。
- **対応（師匠決定）**: A=`execute_command` を **PowerShell 固定**（出力 UTF-8 固定で文字化け解消）／ B=**`list_dir` 追加**（探索で当て推量を排除）／ C=環境プリアンブルは**呼び出し側（`l1_chat`）＋ツールの責務**（L1 は無汚染）／ D=暴走対策は不要＝**L2 の役割**。
- **検証**: 同種のフォルダ読みタスクが `list_dir → read_file → 要約` で正常完了。テスト **34 green**。
