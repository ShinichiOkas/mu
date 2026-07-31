# Design Document: High-Performance Data Processing

## 1. Purpose
This document defines the architecture to achieve data processing (Top-10 extraction and Histogram generation) within a strict 3-second wall-clock limit.

## 2. Structure

### 2.1 File and Module Organization
- **Main Controller**: Orchestrates the flow from file reading to output.
- **Data Reader**: Implements a memory-efficient stream reader.
- **Analysis Engine**: 
    - **Top-10 Processor**: Uses a Min-Heap to maintain the top 10 elements.
    - **Histogram Processor**: Uses fixed-width binning with an array-based counter.
- **Output Formatter**: Formats the results according to specifications.

### 2.2 Data Flow
`Input File` $\rightarrow$ `Generator (Line-by-line)` $\rightarrow$ `Min-Heap (Top 10)` & `Binned Array (Histogram)` $\rightarrow$ `Formatted Output`

### 2.3 Component Responsibilities
- **Data Reader**: Read lines using a generator to avoid loading the entire file into RAM. Use `sys.stdin` or `open()` with a buffer.
- **Top-10 Processor**: 
    - Maintain a heap of size 10.
    - For each new value: If value > `heap[0]`, pop the smallest and push the new value.
    - Time Complexity: $O(N \log 10)$, Space Complexity: $O(10)$.
- **Histogram Processor**:
    - Pre-calculate bin boundaries.
    - Use a fixed-size list (array) where the index represents the bin.
    - Increment the corresponding index based on: `bin_index = (value - min_val) // bin_width`.
    - Time Complexity: $O(N)$, Space Complexity: $O(\text{number of bins})$.

## 3. Quality Characteristics & Realization

### 3.1 Performance (The 3s Limit)
- **Avoid `sort()` on the whole dataset**: This would be $O(N \log N)$ and likely exceed the time limit for large files.
- **Fast I/O**: Use `sys.stdin.readline` or `itertools.islice` for high-throughput reading.
- **Single Pass**: Process both Top-10 and Histogram in one single loop over the data.

### 3.2 Verifiability
To ensure the system is functioning and not silently failing (exit 0 without processing), the following ASCII markers must be printed during the self-test/verification phase:
- `TEST_START`: Printed at the beginning of the verification.
- `TEST_COUNT:[N]`: Printed after processing, where [N] is the number of records processed.
- `TEST_PASS` / `TEST_FAIL`: Printed based on the comparison of the result against the golden sample.
- `PERF_OK`: Printed if the total wall-clock time is $\le 3$ seconds.

## 4. Design Rules

### 4.1 General Rules
- **Input files are READ-ONLY**: Do not modify, overwrite, or delete the input source files.
- **No Temporary Files**: All processing must happen in-memory or via streams. Do not create `.tmp` or `.bak` files.
- **Strict Output**: Only produce the files explicitly required by the specification.

### 4.2 Technical Constraints
- **Top-10 Sort**: Must be implemented via `heapq` (Min-Heap) to ensure $O(N)$ linear-time performance relative to the dataset size.
- **Histogram Binning**: Must be implemented via direct index mapping to an array to ensure $O(1)$ update time per element.
- **Wall-clock limit**: The entire process (Reading $\rightarrow$ Processing $\rightarrow$ Writing) must complete within 3 seconds.

---
**Verification target**: top-10 sort and histogram binning within 3 seconds
