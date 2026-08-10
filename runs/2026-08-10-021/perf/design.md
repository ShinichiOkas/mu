# Design Document: Data Generation and Analysis Scripts

## 1. Structure

### 1.1 File Configuration
- `gen_data.py`: Generates the dataset.
- `analyze.py`: Processes the dataset and outputs results.
- `data.txt`: Input file for `analyze.py` (produced by `gen_data.py`).

### 1.2 Data Flow
`gen_data.py` $\rightarrow$ `data.txt` $\rightarrow$ `analyze.py` $\rightarrow$ Standard Output

### 1.3 Responsibility Division
- **`gen_data.py`**: 
    - Generates 1,000,000 random integers in range $[0, 99999]$.
    - Writes each integer to a new line in `data.txt`.
- **`analyze.py`**:
    - Reads `data.txt` efficiently.
    - Computes the Top 10 largest values.
    - Computes frequency counts for 10 equal-width bins (histogram).
    - Measures elapsed time and outputs results.

---

## 2. Quality Characteristics and Realization

### 2.1 Performance Constraint (3s for 1M entries)
To ensure the processing time is under 3 seconds, the following algorithmic choices are made:

- **Top 10 Calculation**: 
    - **Algorithm**: Min-Heap of size 10.
    - **Reasoning**: Sorting 1M integers takes $O(N \log N)$. A min-heap maintains the top 10 in $O(N \log 10)$, which is effectively $O(N)$. This minimizes memory overhead and CPU cycles.
- **Histogram Calculation**:
    - **Algorithm**: Single-pass array increment.
    - **Reasoning**: While reading each line, the value is mapped to a bucket index: `index = value // 10000`. This is $O(N)$.
- **I/O Optimization**: 
    - Use fast I/O methods (e.g., `sys.stdin` or reading lines in a generator) to avoid loading the entire file into memory as a list if possible, though 1M ints fit in memory. To be safe and fast, a single pass over the file will handle both the heap and the histogram.

### 2.2 Verifiability
- **Time Measurement**: `time.perf_counter()` will be used to capture the precise start and end time.
- **ASCII Markers**: The script must print `ANALYZE OK <seconds>` as the final line. This serves as the machine-readable marker for success and performance verification.

---

## 3. Design Rules

### 3.1 Implementation Rules
- **Input File Immutability**: `analyze.py` must treat `data.txt` as **read-only**. It must not modify, overwrite, or delete the input file.
- **Output Restraint**: Only files specified in the SPEC (`data.txt`) shall be created. No temporary files or logs.
- **Resource Management**: Use `with open(...)` to ensure file handles are closed properly.

### 3.2 Output Formats
- **Top 10**:
    - Header: `Top 10`
    - Format: Values listed in descending order.
- **Histogram**:
    - Header: `Histogram`
    - Format: `[RangeStart, RangeEnd): Count` (e.g., `0-9999: 100230`)
- **Completion Marker**: 
    - Exact string: `ANALYZE OK <elapsed_time>` (e.g., `ANALYZE OK 0.42`)

### 3.3 Algorithmic Specification (analyze.py)
1. Initialize a min-heap `h = []` and an array `bins = [0] * 10`.
2. For each `line` in `data.txt`:
    - Convert `line` to integer `val`.
    - **Histogram**: `bins[val // 10000] += 1` (handle the edge case `val=100000` if it exists, though SPEC says 0-99999).
    - **Top 10**: 
        - If `len(h) < 10`, push `val` to `h`.
        - Else if `val > h[0]`, pop `h[0]` and push `val`.
3. Sort the final `h` in descending order for display.
4. Print results and completion marker.
