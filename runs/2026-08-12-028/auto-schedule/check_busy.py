import subprocess

def check_busy():
    users = ["佐藤", "鈴木", "高橋"]
    log_file = "booking_log.txt"
    
    with open(log_file, "w", encoding="utf-8") as f:
        for user in users:
            # Execute: python outlook.py busy <name>
            result = subprocess.run(["python", "outlook.py", "busy", user], capture_output=True, text=True, encoding="utf-8")
            output = result.stdout
            f.write(f"Busy schedule for {user}:\n{output}\n{'-'*20}\n")
            print(f"Processed {user}")

if __name__ == "__main__":
    check_busy()
