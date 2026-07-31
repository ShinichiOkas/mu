import heapq
import time
import sys

def analyze():
    start_time = time.time()
    
    # Constraints from design.md:
    # - Top-10 via Min-Heap (heapq)
    # - Histogram via array-based counter
    # - Single pass processing
    
    top_10 = []
    bins = [0] * 10  # 0-9999, 10000-19999, ..., 90000-99999
    
    try:
        with open('data.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                val = int(line)
                
                # Top 10 update
                if len(top_10) < 10:
                    heapq.heappush(top_10, val)
                elif val > top_10[0]:
                    heapq.heapreplace(top_10, val)
                
                # Histogram update (0-99999 range)
                # bin_index = (value - min_val) // bin_width
                # Here min_val = 0, bin_width = 10000
                bin_idx = val // 10000
                if 0 <= bin_idx < 10:
                    bins[bin_idx] += 1
                    
    except FileNotFoundError:
        print("Error: data.txt not found")
        return

    # Results
    # Top 10 in descending order
    print("Top 10:")
    sorted_top_10 = sorted(top_10, reverse=True)
    for v in sorted_top_10:
        print(v)
        
    # Histogram
    print("Histogram:")
    for i in range(10):
        lower = i * 10000
        upper = (i + 1) * 10000 - 1
        print(f"{lower}-{upper}: {bins[i]}")
        
    end_time = time.time()
    duration = end_time - start_time
    print(f"ANALYZE OK {duration:.3f}")

if __name__ == "__main__":
    analyze()
