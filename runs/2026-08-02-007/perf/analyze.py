import time
import sys

def main():
    start_time = time.time()
    
    try:
        with open('data.txt', 'r') as f:
            data = [int(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print("data.txt not found")
        return

    if not data:
        print("No data to analyze")
        return

    # Top 10 values in descending order
    top_10 = sorted(data, reverse=True)[:10]
    print("Top 10 values:")
    for val in top_10:
        print(val)

    # 10-bin histogram
    # Assuming bins are based on the range 0-1000 or min-max. 
    # Usually, a 10-bin histogram over the actual data range:
    min_val = min(data)
    max_val = max(data)
    bin_width = (max_val - min_val) / 10 if max_val != min_val else 1
    
    bins = [0] * 10
    for val in data:
        # Find bin index
        if max_val == min_val:
            idx = 0
        else:
            idx = int((val - min_val) / bin_width)
            if idx == 10: # handle max value
                idx = 9
        bins[idx] += 1

    print("\nHistogram:")
    for i in range(10):
        lower = min_val + i * bin_width
        upper = min_val + (i + 1) * bin_width
        print(f"[{lower:.2f}, {upper:.2f}): {bins[i]}")

    end_time = time.time()
    duration = end_time - start_time
    print(f"\nANALYZE OK {duration:.4f}")

if __name__ == "__main__":
    main()
