# Design Document: bugfix for `buggy_stats.py`

## 1. Structure
The goal is to correct the mathematical logic and error handling in `buggy_stats.py` to satisfy the requirements defined in `test_stats.py`.

### Responsibility Map
- `mean(xs)`: Calculate the arithmetic mean. Must raise `ValueError` for empty input.
- `median(xs)`: Calculate the median. Must handle odd/even lengths and raise `ValueError` for empty input.
- `variance(xs)`: Calculate **sample variance** (Bessel's correction: divide by $n-1$). Must raise `ValueError` for $n \le 1$.
- `value_range(xs)`: Calculate the difference between max and min. Must raise `ValueError` for empty input.

## 2. Quality Attributes and Verification Structure
To ensure verification is not dependent solely on exit codes, the implementation process must verify the test results.

- **Verification Method**: Execute `python test_stats.py`.
- **ASCII Marker**: The test runner (unittest) naturally provides a dot `.` for success and `F`/`E` for failure. 
- **Success Criterion**: The output must end with `OK` and the total number of tests executed must match the number of test methods in `TestStats` (9 tests).

## 3. Design Rules
- **Read-Only Inputs**: `test_stats.py` and `SPEC.md` must NOT be modified.
- **Output Scope**: Only `buggy_stats.py` shall be modified.
- **No Side Effects**: No temporary files or logs should be left in the working directory.

## 4. CORRECTIVE LOGIC

### `mean(xs)`
- **Current**: Returns `0` if empty.
- **Fix**: Replace `if not xs: return 0` with `if not xs: raise ValueError("Empty list")`.

### `median(xs)`
- **Current**: Returns the middle element for both odd and even lengths (incorrect for even). Returns `0` if empty.
- **Fix**: 
    1. Replace `if not xs: return 0` with `if not xs: raise ValueError("Empty list")`.
    2. If `len(s)` is odd, return the middle element.
    3. If `len(s)` is even, return the average of the two middle elements.

### `variance(xs)`
- **Current**: Calculates population variance (divides by $n$).
- **Fix**: 
    1. Check if `len(xs) <= 1`. If so, raise `ValueError("Sample variance requires at least two data points")`.
    2. Divide the sum of squares by `len(xs) - 1` instead of `len(xs)`.

### `value_range(xs)`
- **Current**: Only returns `max(xs)`.
- **Fix**: 
    1. If `not xs`, raise `ValueError("Empty list")`.
    2. Return `max(xs) - min(xs)`.
