# Design Document - Task 1

## Requirements
The following core logic and constraints are derived from `test_stats.py` and compared against the goals in `SPEC.md`:

### Core Logic (from test_stats.py)
- **mean**: Calculates the arithmetic mean of a list.
  - Success condition: `mean([1, 2, 3, 4]) == 2.5`.
  - Error handling: Must raise `ValueError` for an empty list (`[]`).
- **median**: Calculates the median of a list (sorted).
  - Odd length: Middle element (e.g., `[3, 1, 2]` -> 2).
  - Even length: Average of two middle elements (e.g., `[1, 2, 3, 4]` -> 2.5).
  - Error handling: Must raise `ValueError` for an empty list (`[]`).
- **variance**: Calculates the sample variance ($\sigma^2 = \frac{\sum(x - \bar{x})^2}{n-1}$).
  - Success condition: `variance([1, 2, 3, 4])` must result in approximately $5/3$.
  - Error handling: Must raise `ValueError` if the sample size is less than 2 (e.g., single value or empty list).
- **value_range**: Calculates the range of values (max - min).
  - Success condition: `value_range([4, 1, 7]) == 6`.
  - Error handling: Must raise `ValueError` for an empty list (`[]`).

### Alignment with SPEC.md
The goal is to fix `buggy_stats.py` so that it satisfies all the above conditions when executed by `test_stats.py`. Specifically, every test case in `test_stats.py` must result in a successful "OK" output and exit code 0.

## Design Rules
Developers must adhere to the following rules:
1. **READ-ONLY FILES**: The file `test_stats.py` is strictly read-only. Do not modify, move, or replace it under any circumstances.
2. **TARGET FILE**: Only `buggy_stats.py` should be modified to fix internal logic.
3. **INTERFACE STABILITY**: Maintain the existing function signatures for `mean`, `median`, `variance`, and `value_range`.
4. **ERROR HANDLING**: Ensure that specific inputs (like empty lists or single-item lists where applicable) trigger a `ValueError` as specified in the requirements.
5. **CLEAN WORKSPACE**: Only produce files explicitly mentioned in the specification. Do not create temporary work files or clutter the directory.
6. **VALIDATION**: The final check is the successful execution of `python test_stats.py`, which must output 'OK'.
