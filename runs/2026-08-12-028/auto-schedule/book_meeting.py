import subprocess
from datetime import datetime, timedelta

def parse_busy_slots(log_text):
    busy_schedules = {}
    current_person = None
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue
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
            except (ValueError, IndexError):
                continue
    return busy_schedules

def is_free(person, start, end, busy_schedules):
    if person not in busy_schedules:
        return True
    for b_start, b_end in busy_schedules[person]:
        if not (end <= b_start or start >= b_end):
            return False
    return True

def find_slot():
    with open('booking_log.txt', 'r', encoding='utf-8') as f:
        log_text = f.read()
    busy_schedules = parse_busy_slots(log_text)
    people = ['佐藤', '鈴木', '高橋']
    dates = ['2026-08-17', '2026-08-18', '2026-08-19', '2026-08-20', '2026-08-21']
    
    # We must avoid 2026-08-20 15:00-16:00 because it is already MTG-001
    for date in dates:
        for hour in range(9, 17):
            start = datetime.strptime(f"{date} {hour:02d}:00", "%Y-%m-%d %H:%M")
            end = start + timedelta(hours=1)
            if date == '2026-08-20' and hour == 15:
                continue
            if all(is_free(p, start, end, busy_schedules) for p in people):
                return date, start.strftime("%H:%M"), end.strftime("%H:%M")
    return None

def main():
    result = find_slot()
    if result:
        date, start, end = result
        print(f"Found slot: {date} {start}-{end}")
        cmd = ['python', 'outlook.py', 'book', '企画会議', date, start, end, '佐藤', '鈴木', '高橋']
        process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        output = process.stdout + process.stderr
        with open('booking_log.txt', 'a', encoding='utf-8') as f:
            f.write('\n' + output)
        print(output)
    else:
        print("No available slot found.")

if __name__ == "__main__":
    main()
