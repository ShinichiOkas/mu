import subprocess
from datetime import datetime, timedelta

def parse_busy_slots(log_text):
    busy_schedules = {}
    current_person = None
    for line in log_text.splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith('---'):
            current_person = line.replace('---', '').strip()
            busy_schedules[current_person] = []
            continue
        if current_person and ' ' in line:
            try:
                parts = line.split(' ')
                date_str = parts[0]
                time_range = parts[1]
                start_str, end_str = time_range.split('-')
                start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
                busy_schedules[current_person].append((start_dt, end_dt))
            except: continue
    return busy_schedules

def is_free(person, start, end, busy_schedules):
    if person not in busy_schedules: return True
    for b_start, b_end in busy_schedules[person]:
        if not (end <= b_start or start >= b_end): return False
    return True

def find_all_slots():
    with open('booking_log.txt', 'r', encoding='utf-8') as f:
        log_text = f.read()
    busy_schedules = parse_busy_slots(log_text)
    people = ['佐藤', '鈴木', '高橋']
    dates = ['2026-08-17', '2026-08-18', '2026-08-19', '2026-08-20', '2026-08-21']
    slots = []
    for date in dates:
        for minute in range(0, 16*60, 15):
            start = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M") + timedelta(minutes=minute)
            end = start + timedelta(hours=1)
            if end.hour > 17 or (end.hour == 17 and end.minute > 0): break
            if all(is_free(p, start, end, busy_schedules) for p in people):
                slots.append((date, start.strftime("%H:%M"), end.strftime("%H:%M")))
    return slots

if __name__ == "__main__":
    print(find_all_slots())
