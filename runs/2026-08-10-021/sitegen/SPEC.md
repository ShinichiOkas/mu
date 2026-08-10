# SPEC — L5（PdM）が目的から定めた仕様
（L5 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
md_src/ にある Markdown 3ファイルから HTML サイトを生成する sitegen.py を作ってくれ。site/ に各ページの .html と、全ページへのリンク一覧を持つ site/index.html を出力する。見出し・箇条書き・リンクが HTML タグに変換されていること。python sitegen.py の実行で 'SITEGEN OK <ページ数>' を表示すること。

## 操作的定義
- **HTML タグに変換されている**: Markdown の見出し (#) が <h1>-<h6>、箇条書き (-) が <ul><li>、リンク [text](url) が <a href="url">text</a> に置換されていること。
- **全ページへのリンク一覧**: site/index.html 内に、md_src/ 内の全 .md ファイルに対応する .html ファイルへの <a> タグによるハイパーリンクが全て含まれていること。

## 受入基準
1. [ ] sitegen.py が存在すること（検査: `Test-Path sitegen.py` → 出力に「True」を含むこと）
2. [ ] python sitegen.py の実行で 'SITEGEN OK <ページ数>' が表示されること（検査: `python sitegen.py` → 出力に「SITEGEN OK」を含むこと）
3. [ ] site/ ディレクトリに .html ファイルが生成されていること（検査: `Get-ChildItem site\*.html`）
4. [ ] site/index.html が存在すること（検査: `Test-Path site\index.html` → 出力に「True」を含むこと）
5. [ ] 生成された HTML に見出しタグ (h1-h6) が含まれていること（検査: `Get-Content site\*.html | Select-String '<h[1-6]>'` → 出力に「<h」を含むこと）
6. [ ] 生成された HTML にリストタグ (ul/li) が含まれていること（検査: `Get-Content site\*.html | Select-String '<ul>' | Select-String '<li>'` → 出力に「<li>」を含むこと）
7. [ ] 生成された HTML にリンクタグ (a href) が含まれていること（検査: `Get-Content site\*.html | Select-String '<a href="'` → 出力に「<a href="」を含むこと）
8. [ ] site/index.html に md_src/ の全ファイルへのリンクが含まれていること

## 仕様
### 目的
md_src/ 内の Markdown ファイルを変換し、静的 HTML サイトを生成するスクリプト sitegen.py を作成する。

### 定義
- **HTML タグに変換されている**: Markdown の見出し (#) → <h1>-<h6>、箇条書き (-) → <ul><li>、リンク [text](url) → <a href="url">text</a> への変換を指す。
- **全ページへのリンク一覧**: site/index.html 内に、md_src/ 内の全ての .md ファイルに対応する .html へのリンクが含まれている状態。

### 仕様
1. **入力**: `md_src/` ディレクトリ内にある Markdown ファイル（.md）。
2. **出力**: `site/` ディレクトリに以下のファイルを生成する。
   - 各 .md ファイルに対応する .html ファイル。
   - 全ページへのリンクをまとめた `site/index.html`。
3. **変換要件**:
   - 見出し、箇条書き、リンクを適切に HTML タグへ変換すること。
4. **実行動作**:
   - `python sitegen.py` を実行した際、標準出力に `SITEGEN OK <ページ数>`（例: SITEGEN OK 3）と表示すること。

### 完了基準 (検収条件)
- `sitegen.py` が存在し、実行して `SITEGEN OK <ページ数>` が出力されること。
- `site/` ディレクトリに各ページの `.html` および `index.html` が生成されていること。
- 生成された HTML 内に `<h[1-6]>`、`<ul>`、`<li>`、`<a href="...">` タグが存在すること。
- `site/index.html` に全ての生成ページへのリンクが記載されていること。
