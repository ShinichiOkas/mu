# PROCESS — L4（PjM）が編んだプロセス（体制表）
（PjM の生成物。役割・人選・順序は仮定を含む。直接編集して直してよい）

## 目的
佐藤・鈴木・高橋の3人が全員参加できる60分の会議『企画会議』を、2026-08-17〜2026-08-21 の営業時間（9:00-17:00）内で見つけて予約してくれ。この環境の予定表サービスは outlook.py（Outlook 風の CLI）で、予定の照会と予約は必ず `python outlook.py` を通すこと（引数なしで実行すると使い方が表示される）。全員の既存の予定と重ならない枠であることが必須。

## タスク列
1. [ ] **secretary** → `availability_analysis.md`
   - task: Extract the busy schedules for 佐藤, 鈴木, and 高橋 from 2026-08-17 to 2026-08-21 using `python outlook.py busy <name>` and identify a common 60-minute free slot within business hours (09:00-17:00).
   - 成功条件: The file must list the busy schedules of all three people and clearly specify a chosen 60-minute slot that does not overlap with any of them and falls within 09:00-17:00.
   - 検査: `Get-Content availability_analysis.md` → 「2026-08-」
2. [ ] **secretary** → `booking_result.md`
   - task: Book the '企画会議' for the identified slot using the command: `python outlook.py book "企画会議" <YYYY-MM-DD> <HH:MM> <HH:MM> 佐藤 鈴木 高橋`.
   - 成功条件: The file must contain the output of the book command showing a 'BOOKED' message.
   - 検査: `Get-Content booking_result.md` → 「BOOKED」
3. [ ] **qa**（model: qwen3.5:9b） → `verdict.md`
   - task: Verify that '企画会議' is correctly booked for the three participants within the specified date range and business hours by running `python outlook.py bookings`.
   - 成功条件: The booking must exist, include 佐藤, 鈴木, and 高橋, be between 2026-08-17 and 2026-08-21, and be within 09:00-17:00. / 判定書が受入基準の**全番号**について『ITEM <番号>: PASS|FAIL|UNCERTAIN — 根拠』を含む。**FAIL / UNCERTAIN を含む判定書も、全番号に根拠が書かれていれば完成である**（成果物の不備を直すのは QA の仕事ではない。不備の事実を書くことが仕事）
   - 検査: `python outlook.py bookings` → 「企画会議」
