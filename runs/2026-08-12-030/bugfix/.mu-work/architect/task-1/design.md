# Design Document

## 1. Structure
- **Module Identification**: The primary logic resides in `buggy_stats.py`.
- **Functions to Implement/Fix**:
  - `mean(data)`: Calculates the arithmetic mean of a list of numbers.
  - `median(data)`: Finds the median value (average of middle two for even length).
  - `variance(data)`: Calculates sample variance ($n-1$ denominator).
  - `value_range(data)`: Returns the range (max - min) of values.

## 2. Required Logic Summary
REQUIRED_LOGIC:
- **Mean**:
  - Input: List of numbers.
  - Action: Sum items and divide by count.
  - Error Handling: Raise `ValueError` if list is empty.
- **Median**:
  - Input: List of numbers.
  - Action: Sort the list first. If length is odd, pick center; if even, average middle two.
  - Error Handling: Raise `ValueError` if list is empty.
- **Variance**:
  - Input: List of numbers.
  - Formula: $\frac{\sum(x_i - \bar{x})^2}{n-1}$ (Sample Variance).
  - Error Handling: Raise `ValueError` if list has fewer than 2 elements.
- **Value Range**:
  - Input: List of numbers.
  - Action: $\max(list) - \min(list)$.
  - Error Handling: Raise `ValueError` if list is empty.

## 3. Quality Attributes and Implementation Structure
- **Validation Strategy**: Every function must be validated by `test_stats.py`.
- **Pass Marking**: Any manual checks or diagnostic outputs should use the following markers:
  - Success indicator for individual calculations (if any are logged): `[OK]`

## 4. Design Rules
- **Input Files are Read-Only**: The file `test_stats.py` must NOT be modified under any circumstances.
- **Minimal Output**: Only files specified in the requirements (`buggy_stats.py`) should be produced/modified. No auxiliary scripts or artifacts should remain.
- **Specific Requirements**: 
  - Ensure floating point precision is handled correctly (use `assertAlmostEqual` context).
  - Handle empty lists by raising `ValueError`.
