# Design Document: Fixes for `buggy_stats.py`

## 1. Structure
The module `buggy_stats.py` provides basic statistical operations. The logic will be corrected to align with the requirements defined in `test_stats.py`.

### Functional Components
- `mean(xs)`: Calculates the arithmetic mean.
- `median(xs)`: Calculates the median value.
- `variance(xs)`: Calculates the sample variance (Bessel's correction).
- `value_range(xs)`: Calculates the range (max - min).

### Data Flow
`Input List [float/int]` $\rightarrow$ `Validation (Empty check)` $\rightarrow$ `Calculation` $\rightarrow$ `Return Value`

---

## 2. Logical Changes (Bug Fixes)

### `mean(xs)`
- **Current**: Returns `0` for empty lists.
- **Requirement**: Must raise `ValueError` for empty lists.
- **Fix**: Replace `if not xs: return 0` with `if not xs: raise ValueError("List cannot be empty")`.

### `median(xs)`
- **Current**: Returns `0` for empty lists. Only returns the middle element for even-length lists.
- **Requirement**: 
    1. Must raise `ValueError` for empty lists.
    2. For even-length lists, return the average of the two middle elements.
- **Fix**: 
    1. Replace `if not xs: return 0` with `if not xs: raise ValueError("List cannot be empty")`.
    2. Implement: `n = len(s)`, if `n % 2 == 0`, return `(s[n//2 - 1] + s[n//2]) / 2`, else return `s[n//2]`.

### `variance(xs)`
- **Current**: Calculates population variance (divides by $n$).
- **Requirement**: Must calculate **sample variance** (divides by $n-1$). Must raise `ValueError` for single-element lists (to avoid division by zero).
- **Fix**: 
    1. Add check: `if len(xs) < 2: raise ValueError("At least two elements required for sample variance")`.
    2. Change divisor from `len(xs)` to `len(xs) - 1`.

### `value_range(xs)`
- **Current**: Returns `max(xs)`.
- **Requirement**: 
    1. Must return the range (`max(xs) - min(xs)`).
    2. Must raise `ValueError` for empty lists.
- **Fix**: 
    1. Add check: `if not xs: raise ValueError("List cannot be empty")`.
    2. Return `max(xs) - min(xs)`.

---

## 3. Quality Attributes & Verification

### Verifiability
The implementation must be verified using the provided `test_stats.py`. 
- **Success Condition**: Execution of `python test_stats.py` must result in an exit code of `0` and the output must contain the string `OK`.

### Test Matrix
| Function | Case | Expected Behavior |
| :--- | :--- | :--- |
| `mean` | Normal | Correct average |
| `mean` | Empty | `ValueError` |
| `median` | Odd length | Middle element |
| `median` | Even length | Average of two middle elements |
| `median` | Empty | `ValueError` |
| `variance`| Normal | Sample variance (n-1) |
| `variance`| Single element | `ValueError` |
| `value_range`| Normal | `max - min` |
| `value_range`| Empty | `ValueError` |

---

## 4. Design Rules

### Constraints
- **Input Files are Read-Only**: `test_stats.py` must not be modified, overwritten, or deleted.
- **No Side Effects**: The module must not create temporary files or modify any global state.
- **Single File Output**: Only `buggy_stats.py` should be modified.

### Implementation Rules
- Use Python 3 standard library only.
- Ensure floating point precision is handled by `unittest.assertAlmostEqual` in the tests; the implementation should use standard division (`/`).
- Raise `ValueError` specifically as required by the test suite.
