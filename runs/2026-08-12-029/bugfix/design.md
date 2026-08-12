# Design Document: Fix for `buggy_stats.py`

## 1. Root Cause Analysis
The current implementation of `buggy_stats.py` fails to meet the requirements defined in `test_stats.py` due to the following causes:

- **`mean(xs)`**: Returns `0` for empty lists instead of raising a `ValueError`.
- **`median(xs)`**: 
    - Returns `0` for empty lists instead of raising a `ValueError`.
    - Incorrectly returns the middle element for even-length lists instead of the average of the two middle elements.
- **`variance(xs)`**: 
    - Calculates population variance (divides by `n`) instead of sample variance (divides by `n-1`).
    - Does not handle the case of a single-element list, which should raise a `ValueError` (division by zero).
- **`value_range(xs)`**: 
    - Returns `max(xs)` instead of the difference between max and min (`max(xs) - min(xs)`).
    - Does not handle empty lists, which should raise a `ValueError`.

## 2. Structural Design & Logic Fixes

### 2.1 Function-level Logic Changes

| Function | Required Change |
| :--- | :--- |
| `mean(xs)` | Replace `if not xs: return 0` with `if not xs: raise ValueError("Empty list")`. |
| `median(xs)` | 1. Replace `if not xs: return 0` with `if not xs: raise ValueError("Empty list")`. <br> 2. For even length `n`, return `(s[n//2 - 1] + s[n//2]) / 2`. <br> 3. For odd length `n`, return `s[n//2]`. |
| `variance(xs)` | 1. Check if `len(xs) < 2` and raise `ValueError("At least two elements required")`. <br> 2. Change divisor from `len(xs)` to `len(xs) - 1`. |
| `value_range(xs)` | 1. Check if `not xs` and raise `ValueError("Empty list")`. <br> 2. Change return value to `max(xs) - min(xs)`. |

### 2.2 Data Flow
Input `xs` (List of numbers) $\rightarrow$ Validation (Empty/Length check) $\rightarrow$ Calculation $\rightarrow$ Return Result.

## 3. Quality Attributes & Verification

### 3.1 Verification Structure
Verification is performed by executing `test_stats.py`. 
The implementer must ensure that all tests in `TestStats` pass.

### 3.2 Verification Marker
To avoid "silent success" (where a script exits 0 without running tests), the implementer must run the tests using `python test_stats.py`. The success is confirmed by the output `OK` provided by `unittest`.

## 4. Design Rules

- **Input File Integrity**: `test_stats.py` is read-only. Do not modify, move, or overwrite it.
- **Artifacts**: Only `buggy_stats.py` should be modified. Do not create temporary files or backup files (e.g., `buggy_stats_bak.py`) in the working directory.
- **Exception Handling**: Always raise `ValueError` when input constraints (empty list, insufficient length) are violated as per the test specifications.
- **Precision**: Use floating point division for mean, median, and variance.
