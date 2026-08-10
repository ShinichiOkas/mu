"""outlook.py — Outlook 風の予定表サービスのモック（検証用の擬似サービス。変更禁止）。

予定の照会・登録は必ずこの CLI を通すこと:

    python outlook.py people                                        参加者の一覧
    python outlook.py busy <name>                                   その人の埋まっている予定
    python outlook.py book <title> <YYYY-MM-DD> <HH:MM> <HH:MM> <name> [<name>...]
                                                                    会議を予約（全員の空きを検査）
    python outlook.py bookings                                      予約済みの会議の一覧

営業時間は 09:00-17:00。既存の予定・予約と重なる予約は CONFLICT で拒否される（exit 1）。
成功すると 'BOOKED <id> <date> <start>-<end>' を表示し bookings.json に保存する。
"""

import json
import sys
from pathlib import Path

_DATA = Path(__file__).with_name("calendar_data.json")
_BOOKINGS = Path(__file__).with_name("bookings.json")
_BUSINESS = ("09:00", "17:00")


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start < b_end and b_start < a_end


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    cal = _load(_DATA, {})

    if cmd == "people":
        print("\n".join(cal))
        return 0

    if cmd == "busy":
        if len(sys.argv) < 3 or sys.argv[2] not in cal:
            print(f"ERROR unknown person: {sys.argv[2] if len(sys.argv) > 2 else '(none)'}")
            return 1
        for e in cal[sys.argv[2]]:
            print(f"{e['date']} {e['start']}-{e['end']} {e['title']}")
        return 0

    if cmd == "bookings":
        bookings = _load(_BOOKINGS, [])
        if not bookings:
            print("(no bookings)")
        for b in bookings:
            print(f"{b['id']} {b['date']} {b['start']}-{b['end']} {b['title']} "
                  f"attendees={','.join(b['attendees'])}")
        return 0

    if cmd == "book":
        if len(sys.argv) < 7:
            print("ERROR usage: book <title> <YYYY-MM-DD> <HH:MM> <HH:MM> <name> [<name>...]")
            return 1
        title, date, start, end, *names = sys.argv[2:]
        if start >= end:
            print(f"ERROR start >= end ({start} >= {end})")
            return 1
        if not (_BUSINESS[0] <= start and end <= _BUSINESS[1]):
            print(f"REJECTED outside business hours {_BUSINESS[0]}-{_BUSINESS[1]}")
            return 1
        for n in names:
            if n not in cal:
                print(f"ERROR unknown person: {n}")
                return 1
            for e in cal[n]:
                if e["date"] == date and _overlaps(start, end, e["start"], e["end"]):
                    print(f"CONFLICT {n} {e['date']} {e['start']}-{e['end']} {e['title']}")
                    return 1
        bookings = _load(_BOOKINGS, [])
        for b in bookings:
            if b["date"] == date and _overlaps(start, end, b["start"], b["end"]) \
                    and set(names) & set(b["attendees"]):
                print(f"CONFLICT existing booking {b['id']}")
                return 1
        booking_id = f"MTG-{len(bookings) + 1:03d}"
        bookings.append({
            "id": booking_id, "title": title, "date": date,
            "start": start, "end": end, "attendees": names,
        })
        _BOOKINGS.write_text(
            json.dumps(bookings, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"BOOKED {booking_id} {date} {start}-{end}")
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
