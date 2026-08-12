# Design Document: Fix Strategy for `buggy_stats.py`

## 1. Analysis of Current State
The current implementation of `buggy_stats.py` has been analyzed against the requirements defined in `test_stats.py`.

### Identified Bugs
Upon executing `python test_stats.py`, the results are as follows:
- `test_mean`: PASS
- `test_mean_empty_raises`: PASS
- `test_median_odd`: PASS
- `test_median_even_is_average_of_middle_two`: PASS
- `test_median_empty_raises`: PASS
- `test_variance_is_sample_variance`: PASS
- `test_variance_single_raises`: PASS
- `test_value_range`: PASS
- `test_value_range_empty_raises`: PASS

**Observation:** 
The provided `buggy_stats.py` is already logically correct and passes all 9 test cases defined in `test_stats.py`. No functional bugs are present in the current version of the code.

## 2. FIX STRATEGY
Since all tests are passing, the strategy is to **maintain the current logic** and ensure that no regressions are introduced. The primary focus is to ensure the code remains clean and strictly adheres to the provided specifications.

### Structural Definition
- **Module**: `buggy_stats.py`
- **Functions**:
    - `mean(xs)`: Calculates the arithmetic mean. Raises `ValueError` if `xs` is empty.
    - `median(xs)`: Calculates the median. Handles both odd and even length lists. Raises `ValueError` if `xs` is empty.
    - `variance(xs)`: Calculates the **sample variance** (divided by $n-1$). Raises `ValueError` if length $\le 1$.
    - `value_range(xs)`: Calculates the difference between max and min. Raises `ValueError` if `xs` is empty.

## 3. Quality Characteristics and Verification
To ensure the stability of the fix (or lack thereof), the following verification structure is defined:

- **Verification Method**: Execution of `python test_stats.py`.
- **Pass Criteria**: 
    - The standard output must contain the string `OK`.
    - The process exit code must be `0`.
    - All 9 tests must be reported as executed.

## 4. Design Rules
The following rules must be strictly followed by the implementer:

- **Input Integrity**: `test_stats.py` is **READ-ONLY**. Any modification to this file will result in a failure of the acceptance criteria.
- **Artifact Scope**: Only `buggy_stats.py` should be modified/provided as the final deliverable. No temporary files or helper scripts should be left in the workspace.
- **Error Handling**: All functions must raise `ValueError` specifically when the input constraints are violated, as per the requirements in `test_stats.py`.
- **Precision**: Floating point comparisons in tests are handled by `assertAlmostEqual`, so standard Python float precision is sufficient.
