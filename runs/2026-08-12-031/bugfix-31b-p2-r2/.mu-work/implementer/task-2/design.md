# Bug-Fix Design: buggy_stats.py

## Root Cause Analysis

The current implementation of `buggy_stats.py` fails several tests in `test_stats.py` due to the following reasons:

1.  **`mean()`**:
    - **Issue**: Returns `0` for an empty list.
    - **Requirement**: Must raise `ValueError` for an empty list.
2.  **`median()`**:
    - **Issue 1**: Returns `0` for an empty list.
    - **Requirement 1**: Must raise `ValueError` for an empty list.
    - **Issue 2**: For even-length lists, it returns the element at `len(s)//2` (the right-middle element).
    - **Requirement 2**: Must return the average of the two middle elements for even-length lists.
3.  **`variance()`**:
    - **Issue 1**: Implements population variance (divides by `n`).
    - **Requirement 1**: Must implement sample variance (divides by `n-1`).
    - **Issue 2**: Does not handle cases where `n-1` would result in division by zero (single element list).
    - **Requirement 2**: Must raise `ValueError` for lists with fewer than 2 elements (specifically single element as per test).
4.  **`value_range()`**:
    - **Issue 1**: Returns `max(xs)` instead of the range (max - min).
    - **Requirement 1**: Must return `max(xs) - min(xs)`.
    - **Issue 2**: Does not handle empty lists.
    - **Requirement 2**: Must raise `ValueError` for an empty list.

---

## Structural Changes

### Logic Updates per Function

#### 1. `mean(xs)`
- Check if `xs` is empty. If so, `raise ValueError`.
- Otherwise, return `sum(xs) / len(xs)`.

#### 2. `median(xs)`
- Check if `xs` is empty. If so, `raise ValueError`.
- Sort the list `s = sorted(xs)`.
- Let `n = len(s)`.
- If `n % 2 == 1`: return `s[n // 2]`.
- If `n % 2 == 0`: return `(s[n // 2 - 1] + s[n // 2]) / 2`.

#### 3. `variance(xs)`
- Check if `len(xs) < 2`. If so, `raise ValueError`.
- Calculate mean `m = mean(xs)`.
- Return `sum((x - m) ** 2 for x in xs) / (len(xs) - 1)`.

#### 4. `value_range(xs)`
- Check if `xs` is empty. If so, `raise ValueError`.
- Return `max(xs) - min(xs)`.

---

## Quality Characteristics & Verification

### Verification Structure
- **Test Execution**: The primary verification is the execution of `python test_stats.py`.
- **Pass Condition**:
    - Exit code must be `0`.
    - Standard output must contain the string `OK`.
- **Regression**: Since `test_stats.py` is the source of truth, no changes to it are permitted.

---

## Design Rules

- **Input Immutability**: The input file `test_stats.py` must be treated as read-only. No modifications, deletions, or recreations are allowed.
- **Output Constraint**: Only `buggy_stats.py` should be modified. No temporary files or helper scripts should be left in the working directory.
- **Error Handling**: All functions must raise `ValueError` explicitly when the input does not meet the mathematical requirements (empty lists or insufficient data for sample variance), rather than returning default values like `0`.
