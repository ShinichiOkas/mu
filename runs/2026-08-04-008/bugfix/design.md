# Design Document: Bug Fixes for buggy_stats.py

## 1. Structure

### File Responsibilities
- `buggy_stats.py`: Contains statistical calculation functions.
    - `mean(xs)`: Calculate the arithmetic mean.
    - `median(xs)`: Calculate the median value.
    - `variance(xs)`: Calculate the sample variance.
    - `value_range(xs)`: Calculate the range (max - min).

### Logic Definition

#### `mean(xs)`
- **Input**: List of numbers `xs`.
- **Behavior**:
    - If `len(xs) == 0`, raise `ValueError`.
    - Return `sum(xs) / len(xs)`.

#### `median(xs)`
- **Input**: List of numbers `xs`.
- **Behavior**:
    - If `len(xs) == 0`, raise `ValueError`.
    - Sort the list `s = sorted(xs)`.
    - Let `n = len(s)`.
    - If `n % 2 == 1`, return `s[n // 2]`.
    - If `n % 2 == 0`, return `(s[n // 2 - 1] + s[n // 2]) / 2`.

#### `variance(xs)`
- **Input**: List of numbers `xs`.
- **Behavior**:
    - If `len(xs) <= 1`, raise `ValueError`.
    - Calculate `mu = mean(xs)`.
    - Calculate sum of squared differences: `sum((x - mu)**2 for x in xs)`.
    - Return `sum_squared_diff / (len(xs) - 1)` (Sample Variance).

#### `value_range(xs)`
- **Input**: List of numbers `xs`.
- **Behavior**:
    - If `len(xs) == 0`, raise `ValueError`.
    - Return `max(xs) - min(xs)`.

## 2. Quality Characteristics and Realization

### Verification
- **Test Execution**: The primary verification is the execution of `python test_stats.py`.
- **Success Marker**: The output must contain the string `OK`.
- **Regression Prevention**: 
    - Ensure that the `test_stats.py` file is not modified.
    - Any temporary files used during implementation must be deleted.

## 3. Design Rules

- **Input Integrity**: The file `test_stats.py` is read-only. Do not modify, overwrite, or delete it.
- **Artifact Control**: Only `buggy_stats.py` shall be modified. No other new files should be created in the working directory.
- **Error Handling**: Use `ValueError` specifically for empty lists or insufficient data (e.g., `len(xs) <= 1` for variance), as required by the tests.
- **Precision**: Use floating point division for means and variances to ensure precision.

---
DESIGN_COMPLETE
