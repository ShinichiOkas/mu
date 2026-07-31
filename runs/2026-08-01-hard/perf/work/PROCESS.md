# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
gen_data.py で 0〜99999 のランダム整数 1,000,000 個を data.txt に書き出し、analyze.py が data.txt を読み込んで値の上位10件と10区間のヒストグラムを表示するようにしてくれ。analyze.py の処理は3秒以内に完了しなければならない。最後に 'ANALYZE OK <経過秒>' を表示すること。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Design the data generation and analysis scripts to handle 1 million integers efficiently, ensuring the analyze.py script completes within the 3-second wall-clock time limit. Specify the data reading and sorting strategy in design.md.
   - 成功条件: The design must specify how to read 1M lines and perform a top-10 sort and histogram binning within 3 seconds.
2. [ ] **implementer** → `gen_data.py`
   - task: Create gen_data.py that generates 1,000,000 random integers in the range [0, 99999] and writes them to data.txt, one per line.
   - 成功条件: Executing the script generates a file named data.txt with exactly 1,000,000 lines.
   - 検査: `python gen_data.py; (Get-Content data.txt | Measure-Object).Count` → 「1000000」
3. [ ] **implementer** → `analyze.py`
   - task: Create analyze.py that reads data.txt, prints the top 10 values in descending order, prints the 10-bin histogram (0-9999, ..., 90000-99999), and ends with 'ANALYZE OK <seconds>'.
   - 成功条件: The script must read 1M integers, output the top 10, output 10 histogram counts, and print 'ANALYZE OK'.
   - 検査: `python analyze.py` → 「ANALYZE OK」
4. [ ] **qa**（model: qwen3.5:cloud） → `verdict.md`
   - task: Verify that gen_data.py creates the correct data size and that analyze.py meets all functional requirements and the 3-second performance constraint.
   - 成功条件: Verification of line count (1M), functional output (Top 10, Histogram), and performance (< 3.0s).
   - 検査: `Measure-Command { python analyze.py } | Select-Object -ExpandProperty TotalSeconds`
