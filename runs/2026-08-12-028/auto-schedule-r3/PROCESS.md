# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [ ] **secretary** → `analysis.md`
   - task: Run `python outlook.py busy` for 佐藤, 鈴木, and 高橋 for the period 2026-08-17 to 2026-08-21. Analyze the results to identify a single 60-minute slot within business hours (09:00-17:00) where all three members are available.
   - 成功条件: The file must list the busy schedules of all three people and explicitly identify one valid 60-minute slot.
   - 検査: `Get-Content analysis.md` → 「2026-08-」
2. [ ] **secretary** → `execution_log.txt`
   - task: Execute the booking command using the identified slot from analysis.md: `python outlook.py book "企画会議" <date> <start_time> <end_time> 佐藤 鈴木 高橋`.
   - 成功条件: The file must contain the output of the booking command confirming the reservation of '企画会議'.
   - 検査: `Get-Content execution_log.txt` → 「企画会議」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that '企画会議' is correctly booked for the 3 specified participants within the target date range and business hours, and ensure no dummy or extra bookings exist.
   - 成功条件: The verdict must be 'PASS' if all criteria in the SPEC are met, and 'FAIL' otherwise. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
