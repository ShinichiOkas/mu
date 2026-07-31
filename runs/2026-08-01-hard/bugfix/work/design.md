# Architectural Design Document: bugy_stats.py Fix

## 1. Structure

### File Configuration
- `buggy_stats.py`: The target module for bug fixes.
- `test_stats.py`: Read-only test suite.

### Responsibility Mapping
The `buggy_stats.py` module provides basic statistical functions. Each function's responsibility is mapped to the test requirements:

- **`mean(xs)`**:
  - Responsibility: Calculate the arithmetic mean of a list of numbers.
  - Fix: Raise `ValueError` if the input list `xs` is empty (currently returns 0).

- **`median(xs)`**:
  - Responsibility: Calculate the median of a list of numbers.
  - Fix 1: Raise `ValueError` if the input list `xs` is empty (currently returns 0).
  - Fix 2: For lists with an even number of elements, return the average of the two middle elements (currently returns the upper middle element).

- **`variance(xs)`**:
  - Responsibility: Calculate the **sample variance** (Bessel's correction).
  - Fix 1: Change the denominator from `len(xs)` to `len(xs) - 1`.
  - Fix 2: Raise `ValueError` if the list has fewer than 2 elements (division by zero or insufficient data for sample variance).

- **`value_range(xs)`**:
  - Responsibility: Calculate the difference between the maximum and minimum values.
  - Fix 1: Calculate `max(xs) - min(xs)` (currently returns only `max(xs)`).
  - Fix 2: Raise `ValueError` if the input list `xs` is empty.

### Data Flow
Input List (`xs`) $\rightarrow$ Validation (Empty/Size check) $\rightarrow$ Calculation $\rightarrow$ Return Result.

## 2. Quality Characteristics and Realization Structure

### Testability and Verification
The success of the implementation is verified by the external test suite `test_stats.py`. 

- **Verification Method**: Execution of `python test_stats.py`.
- **Success Marker**: The standard output must contain the string `OK`.
- **Failure Handling**: Any `ValueError` or `AssertionError` raised by the tests must be treated as a failure.

### Robustness
- The functions must explicitly handle edge cases (empty lists, single-element lists for variance) by raising `ValueError` as specified by the test suite.

## 3. Design Rules

The implementer must adhere to the following rules strictly:

- **Input File Immutability**: `test_stats.py` is **READ-ONLY**. Any modification to this file will result in an immediate failure of the task.
- **Deliverable Constraint**: Only `buggy_stats.py` may be modified. Do not create temporary files or auxiliary scripts in the working directory.
- **Exception Types**: Only `ValueError` should be used for the specified edge cases to satisfy the `unittest.assertRaises(ValueError)` requirements.
- **Precision**: Use floating-point division for mean, median, and variance to satisfy `assertAlmostEqual`.

---
**DESIGN COMPLETE**
