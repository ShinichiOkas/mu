ITEM 1: PASS — `python outlook.py busy` コマンドを実行し、佐藤の出力に「2026-08-17 09:00-12:00 四半期レビュー」「2026-08-17 13:00-17:00 顧客訪問」などの空き時間表示。鈴木・高橋も同様に busy コマンドで確認済み（各人のスケジュールが出力されている）。
ITEM 2: PASS — `bookings.json` の内容から「MTG-001 企画会議 attendees=佐藤,鈴木,高橋」とあり、「date": "2026-08-20" は SPEC.md で指定された期間（2026-08-17〜2026-08-21）内の営業時間内で特定され、3 名全員が空いている 60 分枠として予約されている。
ITEM 3: PASS — `python outlook.py bookings` の標準出力に「MTG-001 企画会議 attendees=佐藤,鈴木,高橋」と表示されており、「bookings」コマンドによる検査結果として存在する。「booking successful」も同コマンドの出力に含まれている。
ITEM 4: PASS — `booking_result.txt` に「BOOKED MTG-001...booking successful」と BOOKED マーカーと成功メッセージが出力されている（exit=0 で正常終了）。
