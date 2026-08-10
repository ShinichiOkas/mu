# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [ ] **architect** → `design.md`
   - task: Analyze the schedules of Sato, Suzuki, and Takahashi for the period 2026-08-17 to 2026-08-21. Identify a 60-minute window between 09:00 and 17:00 where all three are available, avoiding all busy slots. Document the identified slot and the exact command to be used for booking.
   - 成功条件: The document must specify a start and end time for '企画会議' that does not overlap with any busy times for the three members and falls within 09:00-17:00.
2. [ ] **implementer** → `booking_log.txt`
   - task: Execute the booking command specified in design.md to reserve '企画会議' for Sato, Suzuki, and Takahashi.
   - 成功条件: The log must show the successful execution of the 'python outlook.py book' command.
   - 検査: `Get-Content booking_log.txt` → 「python outlook.py book "企画会議"」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that '企画会議' is correctly booked within the specified period and includes all three required participants using the provided outlook.py tool.
   - 成功条件: Confirm the existence of the meeting and the presence of all three names in the bookings list. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python outlook.py bookings` → 「企画会議」
