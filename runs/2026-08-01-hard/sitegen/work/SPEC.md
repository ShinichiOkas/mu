# SPEC — L4（PdM）が目的から定めた仕様
（L4 の生成物。定義・受入基準は仮定を含む。直接編集して直してよい）

## 目的（人間の入力・原文）
md_src/ にある Markdown 3ファイルから HTML サイトを生成する sitegen.py を作ってくれ。site/ に各ページの .html と、全ページへのリンク一覧を持つ site/index.html を出力する。見出し・箇条書き・リンクが HTML タグに変換されていること。python sitegen.py の実行で 'SITEGEN OK <ページ数>' を表示すること。

## 操作的定義
- **Markdown 3ファイル**: md_src/ ディレクトリ内に存在する、拡張子が .md である任意の3つのファイル。
- **HTML サイト**: site/ ディレクトリ内に、入力ファイルと同数の .html ファイルおよび index.html が生成された状態。
- **HTML タグに変換**: Markdown の # (h1), ## (h2), * or - (li), [text](url) (a) が、それぞれ <h1>, <h2>, <li>, <a> タグに置換されていること。

## 受入基準
- [ ] sitegen.py が実行され、正しくページ数を表示すること（検査: `python sitegen.py` → 出力に「SITEGEN OK 3」を含むこと）
- [ ] site/index.html が存在し、3つのページへのリンクが含まれていること（検査: `Get-Content site/index.html` → 出力に「<a>」を含むこと）
- [ ] 変換後のHTMLにMarkdown要素（見出し・箇条書き・リンク）のタグが含まれていること（検査: `Get-ChildItem site/*.html | Get-Content` → 出力に「<h1>」を含むこと）
- [ ] 変換後のHTMLにリストタグが含まれていること（検査: `Get-ChildItem site/*.html | Get-Content` → 出力に「<li>」を含むこと）

## 仕様
Create a Python script `sitegen.py` that converts Markdown files into an HTML site.

### Definitions
- Markdown 3 files: 3 files with .md extension located in `md_src/`.
- HTML Site: A directory `site/` containing converted `.html` files and an `index.html` file.
- Conversion: Markdown syntax for headers (#, ##), lists (*, -), and links ([text](url)) must be converted to `<h1>`, `<h2>`, `<li>`, and `<a>` tags respectively.

### Requirements
1. Input: Read all .md files from the `md_src/` directory.
2. Output:
   - For each `page.md`, create `site/page.html` with the converted content.
   - Create `site/index.html` which contains a list of links to all generated HTML pages.
3. Execution:
   - The script must be runnable via `python sitegen.py`.
   - Upon successful completion, it must print the exact string: `SITEGEN OK 3` (assuming 3 pages).

### Deliverables
- `sitegen.py`: The source code for the generator.

### Verification Criteria
- Execution of `python sitegen.py` must output `SITEGEN OK 3`.
- `site/index.html` must be created and contain `<a>` tags.
- Generated `.html` files in `site/` must contain `<h1>`, `<h2>`, `<li>`, and `<a>` tags where applicable.
