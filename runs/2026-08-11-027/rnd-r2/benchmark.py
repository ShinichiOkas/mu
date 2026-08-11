import time
import collections
import sys
import platform

def benchmark():
    scales = [10**4, 10**5, 10**6]
    
    with open("raw_data.txt", "w", encoding="utf-8") as f:
        f.write(f"Python version: {sys.version}\n")
        f.write(f"OS: {platform.system()} {platform.release()} {platform.version()}\n")
        f.write(f"Processor: {platform.processor()}\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Scale':>10} | {'list.insert(0) (seconds)':>25} | {'deque.appendleft (seconds)':>25}\n")
        f.write("-" * 70 + "\n")

        for n in scales:
            # Measure deque.appendleft (O(1))
            dq = collections.deque()
            start_time = time.perf_counter()
            for i in range(n):
                dq.appendleft(i)
            deque_duration = time.perf_counter() - start_time

            # Measure list.insert(0) (O(n))
            if n <= 10**5:
                lst = []
                start_time = time.perf_counter()
                for i in range(n):
                    lst.insert(0, i)
                list_duration = time.perf_counter() - start_time
                list_res = f"{list_duration:15.6f} seconds"
            else:
                list_res = "Too slow (O(n^2))"

            line = f"{n:10d} | {list_res:>25} | {deque_duration:15.6f} seconds\n"
            f.write(line)
            f.flush()

if __name__ == "__main__":
    benchmark()
