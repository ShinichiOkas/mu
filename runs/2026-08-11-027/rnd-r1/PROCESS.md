# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
Python でリストの先頭に要素を大量に挿入するとき、list.insert(0, x) と collections.deque の appendleft のどちらがどの程度速いかを、実験で決着させてくれ。仮説を立て、計測実験を設計・実施し、結果の数値に基づいて評価した報告書 report.md にまとめること。計測は再現可能なスクリプトとして残し、報告書に載せる数値はそのスクリプトの実出力と一致していること。

## タスク列
1. [x] **scientist** → `experiment_design.md`
   - task: Design the performance experiment to compare `list.insert(0, x)` and `collections.deque.appendleft()` with 100,000+ insertions, specifying the measurement methodology and the required sections for the report.
   - 成功条件: The design must specify 100,000+ items, the two methods to be compared, and the structure for report.md (Hypothesis, Design, Results, Evaluation).
   - 検査: `Get-Content experiment_design.md` → 「100,000」
2. [x] **experimenter** → `benchmark.py`
   - task: Implement a reproducible Python script `benchmark.py` based on the design. The script must measure and print the execution time for both `list.insert(0, x)` and `collections.deque.appendleft()`.
   - 成功条件: The script must be executable and output the time taken for both methods.
   - 検査: `python benchmark.py` → 「insert」
3. [ ] **experimenter** → `raw_results.txt`
   - task: Run `benchmark.py` and record the raw output to a data file for report generation.
   - 成功条件: The file must contain the output of the benchmark script.
   - 検査: `Get-Content raw_results.txt` → 「appendleft」
4. [ ] **scientist** → `report.md`
   - task: Analyze the raw results and write `report.md`. Include: Hypothesis, Experiment Design (Python version, item count), Results (transcribed from raw_results.txt), and Evaluation/Conclusion.
   - 成功条件: Report must contain sections '仮説', '評価' (or '結論'), and the numerical results for both 'insert' and 'appendleft'.
   - 検査: `Get-Content report.md` → 「仮説」
5. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that benchmark.py and report.md exist, that report.md contains all required sections and keywords, and that the numbers in report.md exactly match the output of benchmark.py.
   - 成功条件: All criteria in the SPEC must be satisfied. Final verdict must be 'PASS' or 'FAIL'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
