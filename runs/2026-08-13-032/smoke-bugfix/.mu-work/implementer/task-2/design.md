# Design Document: Bug Fix for `buggy_stats.py`

## 1. Root Cause Analysis
The current implementation of `buggy_stats.py` fails several tests in `test_stats.py` due to the following discrepancies:

### `mean(xs)`
- **Current Behavior**: Returns `0` for an empty list.
- **Required Behavior**: Must raise a `ValueError` for an empty list.
- **Root Cause**: Incorrect handling of empty input; returning a default value instead of raising an exception.

### `median(xs)`
- **Current Behavior**: 
    1. Returns `0` for an empty list.
    2. Always returns the element at `len(s) // 2` (the upper middle element for even-length lists).
- **Required Behavior**: 
    1. Must raise a `ValueError` for an empty list.
    2. For even-length lists, it must return the average of the two middle elements.
- **Root Cause**: Logic fails to account for even-sized datasets and incorrect empty-list handling.

### `variance(xs)`
- **Current Behavior**: Calculates population variance (divides by `n`).
- **Required Behavior**: Must calculate **sample variance** (divides by `n - 1`). Also must raise `ValueError` if the list has only one element (as $n-1=0$).
- **Root Cause**: Use of population variance formula instead of sample variance formula.

### `value_range(xs)`
- **Current Behavior**: Returns `max(xs)`.
- **Required Behavior**: 
    1. Returns the difference between max and min (`max(xs) - min(xs)`).
    2. Must raise `ValueError` for empty lists.
- **Root Cause**: Incorrect formula implemented (returning max instead of range) and missing empty-list check.

---

## 2. Specific Logic Changes

### `mean(xs)`
- Remove `if not xs: return 0`.
- Add check: `if not xs: raise ValueError("Empty list")`.

### `median(xs)`
- Remove `if not xs: return 0`.
- Add check: `if not xs: raise ValueError("Empty list")`.
- If `len(s)` is odd: return `s[n // 2]`.
- If `len(s)` is even: return `(s[n // 2 - 1] + s[n // 2]) / 2`.

### `variance(xs)`
- Add check: `if len(xs) <= 1: raise ValueError("List must contain at least two elements")`.
- Change divisor from `len(xs)` to `len(xs) - 1`.

### `value_range(xs)`
- Add check: `if not xs: raise ValueError("Empty list")`.
- Change return value to `max(xs) - min(xs)`.

---

## 3. Design Rules

### Input/Output Constraints
- **Input Files**: `test_stats.py` is **read-only**. Any modification to this file will result in a failure.
- **Deliverables**: Only `buggy_stats.py` shall be modified.
- **Workdir**: No temporary files should be left in the workspace.

### Quality Characteristics
- **Verification**: The implementation is verified by executing `python test_stats.py`.
- **Success Marker**: The execution must produce the output string `OK` and exit with code `0`.
- **Testing Scope**: All unit tests in `TestStats` (mean, median, variance, value_range) must pass.
