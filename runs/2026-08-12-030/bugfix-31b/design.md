# Design Document: Fix for buggy_stats.py

## Bugs Identified
The following bugs were identified by comparing `buggy_stats.py` with the requirements in `test_stats.py`:

1. **`mean(xs)`**:
   - **Bug**: Returns `0` for empty lists.
   - **Requirement**: Must raise `ValueError` for empty lists.

2. **`median(xs)`**:
   - **Bug 1**: Returns `0` for empty lists.
   - **Requirement 1**: Must raise `ValueError` for empty lists.
   - **Bug 2**: Always returns the element at `len(s)//2` (the upper middle).
   - **Requirement 2**: For even-length lists, it must return the average of the two middle elements.

3. **`variance(xs)`**:
   - **Bug 1**: Calculates population variance (divides by `n`).
   - **Requirement 1**: Must calculate sample variance (divides by `n-1`).
   - **Bug 2**: Does not handle the case where `len(xs) <= 1` (would result in division by zero if using `n-1`).
   - **Requirement 2**: Must raise `ValueError` when only one element is provided.

4. **`value_range(xs)`**:
   - **Bug 1**: Only returns `max(xs)`.
   - **Requirement 1**: Must return the range (max - min).
   - **Bug 2**: Does not handle empty lists.
   - **Requirement 2**: Must raise `ValueError` for empty lists.

## Structural Plan for the Fix

### 1. `mean(xs)`
- Change the empty list check to raise `ValueError` instead of returning `0`.

### 2. `median(xs)`
- Change the empty list check to raise `ValueError`.
- Implement logic to check if the length of the sorted list is odd or even.
- If even: average the two middle elements.
- If odd: return the middle element.

### 3. `variance(xs)`
- Check if `len(xs) < 2`. If so, raise `ValueError`.
- Calculate the sum of squared differences from the mean.
- Divide by `len(xs) - 1` instead of `len(xs)`.

### 4. `value_range(xs)`
- Check if the list is empty. If so, raise `ValueError`.
- Return `max(xs) - min(xs)`.

## Design Rules

### Input/Output Constraints
- **Input files are read-only**: `test_stats.py` must not be modified under any circumstances.
- **Artifacts**: Only `buggy_stats.py` shall be modified. No temporary files should be left in the workspace.

### Quality Assurance
- **Verification**: Success is defined as executing `python test_stats.py` in PowerShell, receiving an output containing "OK", and an exit code of 0.
- **Validation Marker**: The final verification must confirm that the `unittest` framework reports all tests passed.
