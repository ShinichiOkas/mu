# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [x] **architect** → `design.md`
   - task: Analyze the provided calendar_data.json and outlook.py to design a strategy for identifying a free 60-minute slot for Sato, Suzuki, and Takahashi between 2026-08-17 and 2026-08-21 (09:00-17:00). Define the exact parameters and commands needed to execute the booking via outlook.py.
   - 成功条件: The design must specify how to check schedules for all three users and the exact command to book '企画会議'.
   - 検査: `Get-Content design.md` → 「企画会議」
2. [ ] **implementer** → `book_meeting.py`
   - task: Implement a script to find the first available 60-minute slot for the three users within the specified date range and business hours. The script must then call `python outlook.py` with the required arguments to book the '企画会議'.
   - 成功条件: The script must identify a valid slot and successfully execute the booking command.
   - 検査: `python book_meeting.py` → 「Success」
3. [x] **implementer** → `execution_log.txt`
   - task: Execute the booking script to finalize the reservation in the outlook system.
   - 成功条件: The output of the booking script must be recorded, showing a successful booking.
   - 検査: `Get-Content execution_log.txt` → 「Success」
4. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that the '企画会議' is correctly registered by listing the appointments. Additionally, verify that the booked slot does not overlap with any existing appointments for the three users based on the initial data.
   - 成功条件: The output of 'python outlook.py list' must contain '企画会議'. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python outlook.py list` → 「企画会議」
