# Design Document: Correction of `buggy_stats.py`

## 1. Structure

### File Composition
- `buggy_stats.py`: Contains statistical calculation functions (`mean`, `median`, `variance`, `value_range`).

### Responsibilities and Logic Definition
Each function in `buggy_stats.py` must be updated to match the requirements implicit in `test_stats.py`.

#### A. `mean(xs)`
- **Current Logic**: Returns `0` if `xs` is empty.
- **Required Logic**: 
    - If `xs` is empty, raise `ValueError`.
    - Otherwise, return the arithmetic mean: `sum(xs) / len(xs)`.

#### B. `median(xs)`
- **Current Logic**: Returns the middle element of a sorted list. Returns `0` if empty.
- **Required Logic**:
    - If `xs` is empty, raise `ValueError`.
    - If the length of `xs` is odd, return the middle element.
    - If the length of `xs` is even, return the average of the two middle elements.

#### C. `variance(xs)`
- **Current Logic**: Calculates population variance (divided by `n`).
- **Required Logic**:
    - Calculate **sample variance** (divided by `n - 1`).
    - If the length of `xs` is less than 2 (specifically 1 as per `test_variance_single_raises`), raise `ValueError` to avoid division by zero and satisfy the test case.

#### D. `value_range(xs)`
- **Current Logic**: Returns `max(xs)`.
- **Required Logic**:
    - If `xs` is empty, raise `ValueError`.
    - Return the difference between the maximum and minimum values: `max(xs) - min(xs)`.

### Data Flow
Input: List of numbers (`xs`) $\rightarrow$ Processing: Calculation logic $\rightarrow$ Output: Numeric result or `ValueError`.

## 2. Quality Attributes and Realization Structure

### Verifiability
The correctness of the implementation is verified by the external test suite `test_stats.py`. 
- **Success Criterion**: The command `python test_stats.py` must output `OK`.
- **Verification Mechanism**: Since `test_stats.py` uses `unittest`, a successful run will print the total number of tests and "OK".

### Robustness
- Error handling for empty lists or insufficient data points is explicitly defined as raising `ValueError` to ensure the system does not return misleading values (like `0`) when calculations are mathematically undefined or contextually invalid.

## 3. Design Rules

The following rules must be strictly followed by the implementer:

- **Input files are read-only**: `test_stats.py` and `SPEC.md` must not be modified, edited, or deleted under any circumstances.
- **Limited Scope**: Only `buggy_stats.py` is to be modified. No temporary files or auxiliary scripts should be left in the working directory.
- **Error Handling**: Use `raise ValueError()` for invalid inputs as specified in the logic section.
- **Precision**: Use floating-point division to ensure `assertAlmostEqual` passes in the test suite.
- **ASCII Markers**: While not required for the function output, if a self-test script were implemented, it must print the count of executed tests and a result marker (e.g., `[PASS]`). However, for this task, the primary marker is the `OK` output from `test_stats.py`.
