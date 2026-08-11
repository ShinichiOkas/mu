# Experiment Design: `list.insert(0, x)` vs `collections.deque.appendleft()`

## 1. Operationalization of the Hypothesis
**Question:** Which method is more efficient for inserting elements at the beginning of a sequence when the number of items is large (100,000+)?

**Hypothesis:** `collections.deque.appendleft()` will exhibit significantly lower execution time than `list.insert(0, x)` as the number of elements increases.

**Operational Definition:**
- **Metric:** Wall-clock execution time (seconds) for the total insertion process.
- **Support Condition:** The hypothesis is supported if the total time for `deque.appendleft()` is lower than `list.insert(0, x)` by at least one order of magnitude for $N \ge 100,000$.
- **Rejection Condition:** The hypothesis is rejected if there is no statistically significant difference in execution time or if `list.insert(0, x)` is faster.

## 2. Experimental Design

### 2.1 Measurement Methodology
- **Environment:** 
    - Python 3.x (standard CPython implementation).
    - Hardware: Same machine for both tests to ensure consistency.
- **Test Cases:**
    - $N = 1,000$ (Baseline)
    - $N = 10,000$ (Intermediate)
    - $N = 100,000$ (Target)
    - $N = 200,000$ (Stress test)
- **Procedure:**
    1. Initialize an empty `list` and an empty `deque`.
    2. Use the `time.perf_counter()` function to measure the start and end time of the insertion loop.
    3. Run each test case 5 times and calculate the average execution time to minimize noise.
    4. Ensure no other heavy processes are running in the background.

### 2.2 Implementation Detail (Pseudocode)
```python
import time
from collections import deque

def measure_list_insert(n):
    lst = []
    start = time.perf_counter()
    for i in range(n):
        lst.insert(0, i)
    return time.perf_counter() - start

def measure_deque_appendleft(n):
    dq = deque()
    start = time.perf_counter()
    for i in range(n):
        dq.appendleft(i)
    return time.perf_counter() - start
```

## 3. Report Structure (`report.md`)
The final report must contain the following sections:

1. **Hypothesis**: 
    - Statement of the original hypothesis and the defined support/rejection conditions.
2. **Design**: 
    - Description of the environment, the value of $N$ used (100,000+), and the measurement procedure.
3. **Results**: 
    - A table containing the raw execution times (mean and standard deviation) for both methods across all $N$ values.
4. **Evaluation**: 
    - Comparison of results against the operational definition.
    - Final conclusion (Supported/Rejected) based solely on the numerical evidence.
    - Theoretical explanation (e.g., $O(n)$ vs $O(1)$ complexity).
