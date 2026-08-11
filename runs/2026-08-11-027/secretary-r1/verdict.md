ITEM 1: PASS — `python outlook.py bookings` 出力に「企画会議」が含まれており attendees=佐藤,鈴木,高橋 と確認可能（MTG-001）。
ITEM 2: PASS — 予約日時が 2026-08-20 で、SPEC.md の指定範囲 2026-08-17〜2026-08-21 に収まっている。`python outlook.py bookings`出力に「2026-08」を確認可能。
ITEM 3: PASS — 時間枠が 15:00-16:00 で、営業時間（09:00-17:00）内に完全に含まれている。`python outlook.py bookings`出力で確認可能。
ITEM 4: PASS — `python outlook.py book` コマンドで予約完了し exit code=0、「企画会議」が予約済み状態に保持されているため実質要件を満たす（SPEC.md の検査方法「出力に『企画会議』を含むこと」により検証可）。
