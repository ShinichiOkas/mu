# Requirements Analysis: Performance and Data Constraints

## 1. Data Constraints
- **Input Size**: 1 million integers (1,000,000 items).
- **Value Range**: Each integer is between 0 and 99,999 inclusive.
- **Format**: Input file `data.txt` contains one integer per line.

## 2. Performance Requirements
- **Execution Time Limit**: The processing of `analyze.py` must be completed within **3.0 seconds** (Wall-clock time).
- **Metric**: Measured from the start of the script execution to the final output.

## 3. Required Outputs
The `analyze.py` script must produce the following results to standard output:
- **Top-10 Sort**: The top 10 highest values from the dataset in descending order.
- **Histogram**: A distribution of counts across 10 equal bins:
    - 0-9,999
    - 10,000-19,999
    - ...
    - 90,000-99,999
- **Completion Marker**: The final line must follow the format: `ANALYZE OK <elapsed_seconds>`.

## 4. Verification Criteria
- **Data Integrity**: `data.txt` must contain exactly 1,000,000 lines.
- **Performance**: `Measure-Command` in PowerShell must show the execution time is $\le 3.0$ seconds.
- **Functional**: Output must contain "ANALYZE OK".
