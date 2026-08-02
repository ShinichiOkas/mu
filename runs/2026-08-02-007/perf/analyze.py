import time

def main():
    start_time = time.time()
    
    try:
        with open('data.txt', 'r') as f:
            data = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: data.txt not found")
        return

    if not data:
        print("Error: data.txt is empty")
        return

    # Compute top 10 values
    top_10 = sorted(data, reverse=True)[:10]
    print("Top 10 values:")
    for val in top_10:
        print(val)

    # Create a 10-bin histogram
    min_val = min(data)
    max_val = max(data)
    bin_size = (max_val - min_val) / 10
    bins = [0] * 10

    for val in data:
        # Calculate bin index
        if bin_size == 0:
            idx = 0
        else:
            idx = int((val - min_val) / bin_size)
            if idx == 10: # Handle the maximum value
                idx = 9
        bins[idx] += 1

    print("\nHistogram:")
    for i in range(10):
        lower = min_val + i * bin_size
        upper = min_val + (i + 1) * bin_size
        print(f"[{lower:7.2f}, {upper:7.2f}): {'#' * bins[i]}")

    elapsed_time = time.time() - start_time
    print(f"\nElapsed time: {elapsed_time:.4f}s")
    print("ANALYZE OK")

if __name__ == "__main__":
    main()
