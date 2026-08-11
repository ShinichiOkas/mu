# Design Document: Fix for `buggy_stats.py`

## 1. Bug Analysis
The current implementation of `buggy_stats.py` contains the following bugs and logic discrepancies compared to the requirements defined in `test_stats.py`:

| Function | Current Behavior | Expected Behavior (per `test_stats.py`) | Cause |
| :--- | :--- | :--- | :--- |
| `mean` | Returns `0` for empty lists. | Must raise `ValueError` for empty lists. | Incorrect error handling for empty input. |
| `median` | Returns the middle element for even-length lists. | Must return the average of the two middle elements for even-length lists. | Missing logic for even-length sequences. |
| `median` | Returns `0` for empty lists. | Must raise `ValueError` for empty lists. | Incorrect error handling for empty input. |
| `variance` | Calculates population variance (divides by $n$). | Must calculate sample variance (divides by $n-1$). | Used population variance formula instead of sample variance. |
| `variance` | No check for single-element lists. | Must raise `ValueError` for single-element lists (since $n-1 = 0$). | Missing guard clause for division by zero. |
| `value_range` | Returns `max(xs)`. | Must return `max(xs) - min(xs)`. | Logic for range calculation is incomplete. |
| `value_range` | No check for empty lists. | Must raise `ValueError` for empty lists. | Missing guard clause for empty input. |

## 2. Structure and Logic Fixes

### 2.1 `mean(xs)`
- **Change**: Replace `if not xs: return 0` with a check that raises `ValueError`.
- **Logic**:
  - If `len(xs) == 0`, raise `ValueError`.
  - Otherwise, return `sum(xs) / len(xs)`.

### 2.2 `median(xs)`
- **Change**: Update empty list handling and logic for even-length lists.
- **Logic**:
  - If `len(xs) == 0`, raise `ValueError`.
  - Sort the list `s = sorted(xs)`.
  - Let `n = len(s)`.
  - If `n` is odd, return `s[n // 2]`.
  - If `n` is even, return `(s[n // 2 - 1] + s[n // 2]) / 2`.

### 2.3 `variance(xs)`
- **Change**: Switch from population variance to sample variance and add single-element check.
- **Logic**:
  - If `len(xs) <= 1`, raise `ValueError`.
  - Calculate mean `m = mean(xs)`.
  - Return `sum((x - m) ** 2 for x in xs) / (len(xs) - 1)`.

### 2.4 `value_range(xs)`
- **Change**: Fix the range calculation and add empty list check.
- **Logic**:
  - If `len(xs) == 0`, raise `ValueError`.
  - Return `max(xs) - min(xs)`.

## 3. Quality Characteristics and Verification

### 3.1 Verification Method
- The implementation will be verified by executing `python test_stats.py`.
- **Success Marker**: The standard output must contain the string `OK` and the process must exit with code 0.

### 3.2 Design Rules
- **Input files are read-only**: `test_stats.py` MUST NOT be modified, overwritten, or deleted.
- **Targeted modification**: Only `buggy_stats.py` shall be modified.
- **No temporary files**: No scratch files or temporary modules should be left in the working directory.
- **Exact Output**: The success condition is defined strictly by the output of the existing `unittest` runner in `test_stats.py` producing `OK`.
