# Design Document: Bug Fix for `buggy_stats.py`

## BUG_ANALYSIS

Based on the analysis of `buggy_stats.py` and `test_stats.py`, the following bugs and missing requirements were identified:

### 1. `mean(xs)`
- **Bug**: Returns `0` for an empty list.
- **Required Fix**: Must raise `ValueError` when `xs` is empty to satisfy `test_mean_empty_raises`.

### 2. `median(xs)`
- **Bug 1**: Returns `0` for an empty list.
- **Required Fix 1**: Must raise `ValueError` when `xs` is empty to satisfy `test_median_empty_raises`.
- **Bug 2**: Only returns the middle element `s[len(s) // 2]`. For lists with an even number of elements, it does not calculate the average of the two middle elements.
- **Required Fix 2**: For even-length lists, return the average of the two middle elements to satisfy `test_median_even_is_average_of_middle_two`.

### 3. `variance(xs)`
- **Bug 1**: Calculates population variance (divides by `n`).
- **Required Fix 1**: Must calculate sample variance (divide by `n - 1`) to satisfy `test_variance_is_sample_variance`.
- **Bug 2**: Does not handle the case where `len(xs) <= 1`.
- **Required Fix 2**: Must raise `ValueError` when `len(xs) <= 1` to satisfy `test_variance_single_raises`.

### 4. `value_range(xs)`
- **Bug 1**: Returns only `max(xs)` instead of `max(xs) - min(xs)`.
- **Required Fix 1**: Return the difference between maximum and minimum values to satisfy `test_value_range`.
- **Bug 2**: Does not handle empty lists.
- **Required Fix 2**: Must raise `ValueError` when `xs` is empty to satisfy `test_value_range_empty_raises`.

---

## Structure

### File Configuration
- `buggy_stats.py`: Contains the statistical functions. No new files will be created.

### Responsibility Split
- `mean(xs)`: Calculates the arithmetic mean. Raises `ValueError` on empty input.
- `median(xs)`: Calculates the median (handles both odd and even lengths). Raises `ValueError` on empty input.
- `variance(xs)`: Calculates the sample variance. Raises `ValueError` if input size is $\le 1$.
- `value_range(xs)`: Calculates the range (max - min). Raises `ValueError` on empty input.

---

## Quality Characteristics and Realization

### Verifiability
The verification will be performed by executing the existing `test_stats.py`.
- **Success Condition**: Execution of `python test_stats.py` must output `OK` and exit with code 0.
- **Testing Strategy**: All test cases in `unittest.TestCase` within `test_stats.py` must pass.

---

## Design Rules

1. **Input Files are Read-Only**: `test_stats.py` must not be modified, overwritten, or deleted.
2. **Artifacts**: Only `buggy_stats.py` shall be modified. No temporary or working files should be left in the directory.
3. **Error Handling**: Use `ValueError` for all specified error cases as required by the test suite.
4. **Precision**: Use floating point division for mean, median, and variance.
