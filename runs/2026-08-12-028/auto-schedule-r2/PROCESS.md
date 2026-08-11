# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [ ] **secretary** → `availability_analysis.md`
   - task: Execute `python outlook.py busy` for 佐藤, 鈴木, and 高橋 to collect their schedules for the period 2026-08-17 to 2026-08-21. Analyze the gaps within business hours (09:00-17:00) to identify a single 60-minute window where all three are available.
   - 成功条件: The file must list the busy times for all three individuals and clearly identify at least one valid 60-minute slot between 2026-08-17 and 2026-08-21.
   - 検査: `Get-Content availability_analysis.md` → 「2026-08-」
2. [ ] **secretary** → `booking_result.md`
   - task: Using the slot identified in availability_analysis.md, execute the booking command: `python outlook.py book 企画会議 <date> <start> <end> 佐藤 鈴木 高橋`. Verify that the output contains the 'BOOKED' marker.
   - 成功条件: The file must contain the standard output of the booking command, including the 'BOOKED' marker.
   - 検査: `Get-Content booking_result.md` → 「BOOKED」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the '企画会議' is successfully registered in the system by running `python outlook.py bookings` and checking the output against the SPEC requirements.
   - 成功条件: The output of `python outlook.py bookings` must contain '企画会議'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python outlook.py bookings` → 「企画会議」
