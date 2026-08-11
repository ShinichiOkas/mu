import subprocess

def main():
    people = ["佐藤", "鈴木", "高橋"]
    log_file = "booking_log.txt"
    
    # Ensure the log file is empty before starting
    open(log_file, "w", encoding="utf-8").close()
    
    for person in people:
        cmd = ["python", "outlook.py", "busy", person]
        try:
            # Explicitly use utf-8 for capture_output to avoid cp932 issues on Windows
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"--- {person} ---\n")
                f.write(result.stdout if result.stdout else "")
                f.write("\n")
        except subprocess.CalledProcessError as e:
            print(f"Error fetching schedule for {person}: {e}")
        except UnicodeDecodeError:
            # Fallback if utf-8 fails, though outlook.py is expected to be consistent
            result = subprocess.run(cmd, capture_output=True, text=False, check=True)
            decoded_output = result.stdout.decode("utf-8", errors="replace")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(decoded_output)
                f.write("\n")

if __name__ == "__main__":
    main()
