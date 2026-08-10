import json
import subprocess
from datetime import datetime, timedelta

def solve():
    # Load calendar data
    with open("calendar_data.json", "r", encoding="utf-8") as f:
        calendar = json.load(f)

    users = list(calendar.keys())
    if len(users) < 3:
        print("Error: Not enough users in calendar data.")
        return

    # We need to find the first 60-minute slot for the first three users (or all if 3)
    target_users = users[:3]
    
    # Business hours
    biz_start_str = "09:00"
    biz_end_str = "17:00"
    
    # Identify the date range from the calendar data
    all_dates = set()
    for user_events in calendar.values():
        for event in user_events:
            all_dates.add(event["date"])
    
    sorted_dates = sorted(list(all_dates))
    
    for date in sorted_dates:
        # Create a timeline for the day (in 30-min increments for simplicity, 
        # but we need to check 60-min blocks)
        # Better yet: check every 30-min start time from 09:00 to 16:00
        current_time = datetime.strptime(f"{date} {biz_start_str}", "%Y-%m-%d %H:%M")
        end_of_day = datetime.strptime(f"{date} {biz_end_str}", "%Y-%m-%d %H:%M")
        
        while current_time + timedelta(minutes=60) <= end_of_day:
            slot_start = current_time.strftime("%H:%M")
            slot_end = (current_time + timedelta(minutes=60)).strftime("%H:%M")
            
            is_available = True
            for user in target_users:
                for event in calendar.get(user, []):
                    if event["date"] == date:
                        # Check overlap: start1 < end2 and start2 < end1
                        if slot_start < event["end"] and event["start"] < slot_end:
                            is_available = False
                            break
                if not is_available:
                    break
            
            if is_available:
                # Found the first slot!
                # Book the meeting via outlook.py
                # Command: python outlook.py book <title> <YYYY-MM-DD> <HH:MM> <HH:MM> <name> [<name>...]
                cmd = [
                    "python", "outlook.py", "book", 
                    "Common Meeting", date, slot_start, slot_end
                ] + target_users
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and "BOOKED" in result.stdout:
                    print("Success")
                    return
                else:
                    # If it's a conflict with an existing booking, we should continue searching for the next slot
                    # instead of giving up.
                    continue
            
            current_time += timedelta(minutes=30)

    print("No common 60-minute slot found.")

if __name__ == "__main__":
    solve()
