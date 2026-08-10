# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
md_src/ にある Markdown 3ファイルから HTML サイトを生成する sitegen.py を作ってくれ。site/ に各ページの .html と、全ページへのリンク一覧を持つ site/index.html を出力する。見出し・箇条書き・リンクが HTML タグに変換されていること。python sitegen.py の実行で 'SITEGEN OK <ページ数>' を表示すること。

## タスク列
1. [x] **architect** → `design.md`
   - task: Design the sitegen.py script. Define the Markdown to HTML conversion logic for headings (#), lists (-), and links ([text](url)), the directory traversal for md_src/, and the structure of index.html. Ensure the output format 'SITEGEN OK <count>' is planned.
   - 成功条件: Design includes conversion rules, file IO strategy, and the specific output message format.
   - 検査: `Get-Content design.md` → 「SITEGEN OK」
2. [ ] **implementer** → `sitegen.py`
   - task: Implement the sitegen.py script based on design.md. The script must read .md files from md_src/, convert specified Markdown elements to HTML, write them to site/, and generate site/index.html with links to all pages. It must print 'SITEGEN OK <page_count>' on success.
   - 成功条件: Script correctly implements conversion and file generation; prints the required success message.
   - 検査: `python sitegen.py` → 「SITEGEN OK」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the deliverables against the SPEC. Check for: 1. Existence of sitegen.py, 2. Correct stdout on execution, 3. Generation of site/ directory and index.html, 4. Presence of <h1>-<h6>, <ul>, <li>, and <a href> tags in generated HTML, 5. Completeness of links in index.html relative to md_src/ files.
   - 成功条件: All criteria in the SPEC are marked as passed with supporting evidence from the filesystem. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASSED」
