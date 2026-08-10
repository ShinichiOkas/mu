# JSON Parser Design Specification

## 1. Overview
This document defines the architecture for a manual JSON parser implementing recursive descent parsing. The implementation **must not** use the native `json` module or any third-party JSON libraries.

## 2. Structure

### 2.1 File Configuration
- `parser.py`: Contains the `JSONParser` class and the main parsing logic.
- `test_suite.py`: Contains the self-test execution logic and the 20+ test cases.

### 2.2 Data Flow and Responsibility
The parser will use a pointer/index-based approach to traverse the input string.

1. **`JSONParser` Class**:
   - `parse(text)`: Entry point. Initializes the index and calls `parse_value()`.
   - `parse_value()`: Determines the type of the next token and delegates to specific methods:
     - `{` $\rightarrow$ `parse_object()`
     - `[` $\rightarrow$ `parse_array()`
     - `"` $\rightarrow$ `parse_string()`
     - `t`, `f`, `n` $\rightarrow$ `parse_literal()` (true, false, null)
     - `0-9`, `-` $\rightarrow$ `parse_number()`
   - `skip_whitespace()`: Advances the index past spaces, tabs, carriage returns, and line feeds.

### 2.3 Detailed Parsing Logic

#### A. Recursive Structure (Objects & Arrays)
- **Objects**:
  - Matches `{`.
  - While next char is not `}`, call `parse_string()` for the key, expect `:`, then call `parse_value()` for the value.
  - Expect `,` between pairs.
- **Arrays**:
  - Matches `[`.
  - While next char is not `]`, call `parse_value()`.
  - Expect `,` between elements.

#### B. Strings and Escape Sequences (`\uXXXX`)
- Matches opening `"`.
- Reads characters until closing `"`.
- Handle backslash `\` escapes:
  - `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`.
  - **Unicode `\uXXXX`**: 
    - Read 4 hexadecimal digits following `\u`.
    - Convert these digits to an integer.
    - Convert the integer to a character using `chr()`.

#### C. Numbers and Scientific Notation
- Matches optional `-`.
- Integer part: One or more digits (leading zeros allowed only if the number is just `0`).
- Fractional part: Optional `.` followed by one or more digits.
- Exponent part: Optional `e` or `E`, followed by optional `+` or `-`, followed by one or more digits.
- The result must be converted to `int` or `float` accordingly.

## 3. Quality Characteristics & Verification

### 3.1 Self-Test Suite
The `test_suite.py` must implement a test runner that iterates through a list of input-output pairs.
- **Success Marker**: Each test case must print its result. The final summary must print: `TESTS_PASSED: [X]/[Y]`.
- **Failure Handling**: If a test fails, it should print the expected vs actual value.

### 3.2 Test Cases (20+ Cases)
1. `null`
2. `true`
3. `false`
4. Empty object `{}`
5. Empty array `[]`
6. Simple string `"hello"`
7. String with escaped quote `"He said \"Hi\""`
8. String with escaped backslash `"C:\\Path"`
9. Unicode escape `\u0041` (A)
10. Unicode escape `\u3042` (あ)
11. Integer `123`
12. Negative integer `-456`
13. Float `123.456`
14. Negative float `-0.123`
15. Scientific notation `1e10`
16. Scientific notation `1.23E-4`
17. Negative scientific notation `-1.23e+5`
18. Nested array `[1, [2, 3], 4]`
19. Nested object `{"a": {"b": 1}}`
20. Complex mix `{"list": [1, "a", null], "val": 1.2e3}`
21. Array of objects `[{"id":1}, {"id":2}]`
22. Deeply nested structure (3+ levels)

## 4. Design Rules

- **Input Immutability**: The input JSON string must be treated as read-only.
- **No Native JSON**: Use of `import json` or similar libraries is strictly forbidden.
- **Output Constraints**: Only create the files specified in Section 2.1.
- **Whitespace**: Must handle arbitrary whitespace around structural characters (`{`, `}`, `[`, `]`, `:`, `,`).
- **Validation**: The parser should raise a `ValueError` on invalid JSON syntax.

DESIGN_COMPLETE
