# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
md_src/ にある Markdown 3ファイルから HTML サイトを生成する sitegen.py を作ってくれ。site/ に各ページの .html と、全ページへのリンク一覧を持つ site/index.html を出力する。見出し・箇条書き・リンクが HTML タグに変換されていること。python sitegen.py の実行で 'SITEGEN OK <ページ数>' を表示すること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the sitegen.py script. Specify the regex patterns for Markdown conversion (#, ##, *, -, [text](url)), the directory structure for md_src/ and site/, and the logic for generating index.html.
   - 成功条件: The design document must cover the regex mapping and the workflow for processing files.
2. [ ] **implementer** → `sitegen.py`
   - task: Create sample markdown files in md_src/ to test the converter and implement sitegen.py according to the design. The script must convert Markdown to HTML and output 'SITEGEN OK 3'.
   - 成功条件: The script must create the site/ directory, convert all .md files from md_src/, create index.html, and print the required success message.
3. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that the generated site/index.html contains links and that the converted HTML files contain the required tags (<h1>, <h2>, <li>, <a>).
   - 成功条件: All verification criteria from the SPEC must be met, including the output of the execution and the content of the generated HTML files.
