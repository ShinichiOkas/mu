ITEM 1: PASS - bookings.json に「企画会議」というタイトル（id: MTG-001）の予定が記載されていること
ITEM 2: PASS - booking_log.txt で予約日が 2026-08-20 の範囲内であること、bookings.json の date フィールドで確認可能
ITEM 3: PASS - booking_log.txt と bookings.json で開始時刻「15:00」、終了時刻「16:00」は営業時間（09:00-17:00）内に収まっていること
ITEM 4: PASS - start=15:00、end=16:00 の設定により期間がちょうど 60 分であること (booking_log.txt と bookings.json)
ITEM 5: PASS - calendar_data.json から佐藤（製品検討会終了後）、鈴木（リリース作業終了後）、高橋（経営報告資料作成終了後）は 2026-08-20 の 15:00-16:00 に重複予定が一件もないことが確認可能
