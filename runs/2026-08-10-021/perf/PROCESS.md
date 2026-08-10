# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
gen_data.py で 0〜99999 のランダム整数 1,000,000 個を data.txt に書き出し、analyze.py が data.txt を読み込んで値の上位10件と10区間のヒストグラムを表示するようにしてくれ。analyze.py の処理は3秒以内に完了しなければならない。最後に 'ANALYZE OK <経過秒>' を表示すること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the data generation and analysis scripts. Define the algorithm for finding the top 10 values (e.g., using a min-heap or sorting) and the histogram calculation to ensure the 3-second performance constraint is met for 1 million entries.
   - 成功条件: The design must specify how to handle 1,000,000 lines efficiently and the exact format for the histogram and top 10 output.
   - 検査: `Test-Path design.md` → 「True」
2. [ ] **implementer** → `gen_data.py`
   - task: Implement gen_data.py to generate 1,000,000 random integers between 0-99999 and save them to data.txt, one per line.
   - 成功条件: Running the script creates data.txt with exactly 1,000,000 lines of numbers.
   - 検査: `python gen_data.py; (Get-Content data.txt).Count` → 「1000000」
3. [ ] **implementer** → `analyze.py`
   - task: Implement analyze.py to read data.txt, compute the top 10 values and the 10-bucket histogram, and print them. Ensure the output ends with 'ANALYZE OK <seconds>' and the total execution time is under 3 seconds.
   - 成功条件: The script must output 'Top 10', 'Histogram', and end with 'ANALYZE OK'. Execution time must be <= 3s.
   - 検査: `python analyze.py` → 「ANALYZE OK」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify all deliverables against the SPEC. Check if data.txt is correct, analyze.py outputs are accurate (Top 10 and Histogram), and the performance constraint (3s) is strictly honored.
   - 成功条件: The verdict must explicitly state PASS or FAIL for each criterion in the SPEC. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Test-Path verdict.md` → 「True」
