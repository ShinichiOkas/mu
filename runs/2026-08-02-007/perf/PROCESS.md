# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
gen_data.py で 0〜99999 のランダム整数 1,000,000 個を data.txt に書き出し、analyze.py が data.txt を読み込んで値の上位10件と10区間のヒストグラムを表示するようにしてくれ。analyze.py の処理は3秒以内に完了しなければならない。最後に 'ANALYZE OK <経過秒>' を表示すること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the logic for data generation and high-performance analysis. Since 1 million integers are processed, design analyze.py to use efficient sorting or heap for top 10 and a simple frequency array for the histogram to ensure the 3-second time limit is met.
   - 成功条件: The design must specify the use of random.randint for gen_data.py and an efficient approach for analyzing 1 million entries in analyze.py.
2. [x] **implementer** → `gen_data.py`
   - task: Implement gen_data.py to generate 1,000,000 random integers (0-99999) and write them to data.txt.
   - 成功条件: Must produce a file named data.txt with 1,000,000 lines.
   - 検査: `python gen_data.py; (Get-Content data.txt).Count` → 「1000000」
3. [ ] **implementer** → `analyze.py`
   - task: Implement analyze.py to read data.txt, calculate the top 10 values (descending), calculate the 10-bin histogram, and print 'ANALYZE OK <seconds>'.
   - 成功条件: Must process data.txt, output the top 10 and histogram, and finish in under 3 seconds.
   - 検査: `python analyze.py` → 「ANALYZE OK」
4. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that gen_data.py creates a file with exactly 1,000,000 lines and that analyze.py correctly computes the top 10 and histogram within the 3-second time limit, outputting 'ANALYZE OK'.
   - 成功条件: Both scripts must pass the functional and performance requirements specified in the SPEC.
   - 検査: `python gen_data.py; (Get-Content data.txt).Count; python analyze.py` → 「ANALYZE OK」
