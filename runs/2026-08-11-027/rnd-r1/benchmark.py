import time
import collections

def benchmark_insert():
    data = []
    n = 100000
    start = time.time()
    for i in range(n):
        data.insert(0, i)
    end = time.time()
    return end - start

def benchmark_appendleft():
    data = collections.deque()
    n = 100000
    start = time.time()
    for i in range(n):
        data.appendleft(i)
    end = time.time()
    return end - start

if __name__ == "__main__":
    insert_time = benchmark_insert()
    appendleft_time = benchmark_appendleft()
    print(f"list.insert(0, x) time: {insert_time:.6f} seconds")
    print(f"collections.deque.appendleft() time: {appendleft_time:.6f} seconds")
