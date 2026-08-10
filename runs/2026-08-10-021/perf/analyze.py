import heapq
import time
import sys

def analyze():
    start_time = time.perf_counter()
    
    top_10_heap = []
    bins = [0] * 10
    
    try:
        with open('data.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                val = int(line)
                
                # Histogram: Range 0-99999, 10 buckets
                # bucket = val // 10000
                # Handle case where val might be 100000 if it exists
                bucket = val // 10000
                if bucket > 9:
                    bucket = 9
                elif bucket < 0:
                    bucket = 0
                bins[bucket] += 1
                
                # Top 10: Min-Heap
                if len(top_10_heap) < 10:
                    heapq.heappush(top_10_heap, val)
                elif val > top_10_heap[0]:
                    heapq.heapreplace(top_10_heap, val)
                    
    except FileNotFoundError:
        print("Error: data.txt not found")
        return

    # Results processing
    top_10_sorted = sorted(top_10_heap, reverse=True)
    
    print("Top 10")
    for v in top_10_sorted:
        print(v)
        
    print("Histogram")
    for i in range(10):
        start = i * 10000
        end = (i + 1) * 10000 - 1
        print(f"{start}-{end}: {bins[i]}")
        
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"ANALYZE OK {elapsed:.2f}")

if __name__ == "__main__":
    analyze()
