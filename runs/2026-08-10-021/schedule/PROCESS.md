# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [x] **architect** → `design.md`
   - task: Analyze the current schedules of Sato, Suzuki, and Takahashi using `python outlook.py` for the period 2026-08-17 to 2026-08-21. Identify a 60-minute slot between 09:00 and 17:00 where all three are available. Document the selected slot and the verification logic in design.md.
   - 成功条件: The file must specify a valid date and time slot (60 mins, 09:00-17:00) that does not overlap with existing appointments for the three users.
   - 検査: `Get-Content design.md` → 「2026-08-」
2. [x] **implementer** → `booking_log.txt`
   - task: Execute the reservation command via `python outlook.py` to book the '企画会議' (Planning Meeting) for the slot identified in design.md. Record the exact command executed in booking_log.txt.
   - 成功条件: The file must contain the successful command used to book the meeting.
   - 検査: `python outlook.py list` → 「企画会議」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the booked '企画会議' meets all SPEC criteria: 1. Exists in the list. 2. Date is between 2026-08-17 and 2026-08-21. 3. Time is within 09:00-17:00. 4. Duration is exactly 60 minutes. 5. No overlap with existing schedules for the three members.
   - 成功条件: The verdict must explicitly state 'PASS' if all criteria are met, or 'FAIL' with reasons. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `Get-Content verdict.md` → 「PASS」
