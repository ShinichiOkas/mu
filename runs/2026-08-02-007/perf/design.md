# Architecture Design Document: High-Performance Integer Analysis

## 1. Overview
This system generates a dataset of 1 million integers and performs high-performance analysis to extract the top 10 largest values and a frequency histogram.

## 2. Structure
The system consists of two primary Python scripts.

### 2.1 `gen_data.py` (Data Generation)
- **Responsibility**: Generate 1,000,000 random integers and save them to a file.
- **Logic**:
    - Use a loop or list comprehension to generate 1,000,000 integers.
    - **Constraint**: Must use `random.randint(min, max)` for value generation.
    - **Output**: Write each integer to `data.txt`, one per line.
- **Data Flow**: `random.randint` $\rightarrow$ List/Generator $\rightarrow$ `data.txt`.

### 2.2 `analyze.py` (High-Performance Analysis)
- **Responsibility**: Read `data.txt` and compute the Top 10 values and the frequency distribution.
- **Logic**:
    - **Top 10 Extraction**: 
        - To maintain $O(N \log K)$ complexity (where $K=10$), use a **Min-Heap** (via `heapq` module) to track the largest 10 elements.
        - Alternatively, use `heapq.nlargest`.
    - **Histogram Generation**:
        - Use a **Frequency Array** (or `collections.Counter`) to count occurrences of each value.
        - Since the range of integers is defined, an array index represents the value for $O(1)$ access.
- **Performance Target**: Total execution time must be under 3 seconds for 1M elements.
- **Data Flow**: `data.txt` $\rightarrow$ Heap/Frequency Map $\rightarrow$ Standard Output.

## 3. Quality Attributes and Verification
To ensure the implementation is correct and performant, the following verification mechanisms are required.

### 3.1 Performance Verification
- The analysis script must measure its own execution time and print it.
- **Marker**: The output must include `[PERF_TIME: X.XXs]`.

### 3.2 Logic Verification (Self-Test)
- The scripts must output a specific ASCII marker to confirm they successfully processed the target volume of data.
- **Marker**: `[VERIFIED: 1000000_RECORDS]`

## 4. Design Rules
The implementer must strictly adhere to the following rules:

### 4.1 File I/O
- **Input files are read-only**: `analyze.py` must not modify or delete `data.txt`.
- **No temporary files**: Only `data.txt` (output of `gen_data.py`) and the final analysis output are permitted. No `.tmp` or `.log` files.

### 4.2 Algorithmic Constraints
- Use `random.randint` in `gen_data.py`.
- Use a heap-based approach for top-K elements in `analyze.py` to avoid the $O(N \log N)$ cost of sorting the entire 1M array.

### 4.3 Mandatory Output Markers
The following exact strings must be present in the execution output for the QA process:
- `[PERF_TIME: `
- `[VERIFIED: 1000000_RECORDS]`
