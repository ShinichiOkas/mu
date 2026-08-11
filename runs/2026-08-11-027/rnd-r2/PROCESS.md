# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
Python でリストの先頭に要素を大量に挿入するとき、list.insert(0, x) と collections.deque の appendleft のどちらがどの程度速いかを、実験で決着させてくれ。仮説を立て、計測実験を設計・実施し、結果の数値に基づいて評価した報告書 report.md にまとめること。計測は再現可能なスクリプトとして残し、報告書に載せる数値はそのスクリプトの実出力と一致していること。

## タスク列
1. [x] **scientist** → `experiment_design.md`
   - task: Design the performance comparison experiment between list.insert(0) and collections.deque.appendleft. Define the scale of insertions (10^4, 10^5, 10^6), the hypothesis regarding time complexity (O(n) vs O(1)), and the metrics for measurement.
   - 成功条件: The design must specify the exact insertion counts and the theoretical basis for the hypothesis.
   - 検査: `Get-Content experiment_design.md` → 「仮説」
2. [x] **experimenter** → `benchmark.py`
   - task: Implement the benchmark script based on the experiment design. The script must measure wall-clock time for both methods across specified scales using only standard libraries and output the results to stdout.
   - 成功条件: The script must run without errors and produce timing results for both insert(0) and appendleft.
   - 検査: `python benchmark.py` → 「appendleft」
3. [ ] **experimenter** → `raw_data.txt`
   - task: Execute benchmark.py and record the raw output for all specified scales (10^4, 10^5, 10^6). Capture the environment details (Python version, OS).
   - 成功条件: The file must contain the actual execution output of benchmark.py including timing values.
   - 検査: `Get-Content raw_data.txt` → 「seconds」
4. [ ] **scientist** → `report.md`
   - task: Analyze the raw data and write the report. Include the hypothesis, experiment design, raw numerical results in a table, and a conclusion on which method is faster and by what factor.
   - 成功条件: The report must contain '仮説', '結論', and the exact numerical values from raw_data.txt.
   - 検査: `Get-Content report.md` → 「結論」
5. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify the deliverables against the SPEC. Ensure benchmark.py exists, report.md contains required sections, and the numerical data in report.md matches the output of benchmark.py.
   - 成功条件: The verdict must state whether the SPEC is fully satisfied, specifically checking for numerical consistency and presence of conclusion. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
