# Design Document: Recursive Descent JSON Parser

## 1. Structure

### File Composition
The implementation will be contained in a single file: `jsonparse.py`.

### Responsibilities & Data Flow
The parser is structured as a recursive descent parser. It maintains a current position pointer as it consumes the input string.

**Data Flow:**
`Input Text` $\rightarrow$ `Lexer/Tokenizer` $\rightarrow$ `Recursive Descent Parser` $\rightarrow$ `Python Data Structures`

**Component Breakdown:**
- **Parser Class/State**: Maintains `text` and `pos`.
- **`parse()` entry point**: Handles whitespace stripping and calls the value parser.
- **Value Parsers**:
    - `parse_value()`: Dispatcher based on the current character.
    - `parse_object()`: Handles `{ ... }`, recurses into `parse_value()` for values.
    - `parse_array()`: Handles `[ ... ]`, recurses into `parse_value()` for values.
    - `parse_string()`: Handles `" ... "`, processes escape sequences.
    - `parse_number()`: Handles integers, floats, and scientific notation.
    - `parse_constant()`: Handles `true`, `false`, `null`.

### Grammar Definition (EBNF)
```ebnf
value    = object | array | string | number | constant .
object   = "{" [ pair { "," pair } ] "}" .
pair     = string ":" value .
array    = "[" [ value { "," value } ] "]" .
string   = '"' { char } '"' .
char     = any-unicode-char-except-quote-or-backslash | escape .
escape   = "\\" ( '"' | "\\" | "/" | "b" | "f" | "n" | "r" | "t" | "u" hex4 ) .
number   = [ "-" ] int [ frac ] [ exp ] .
int      = digit { digit } .
frac     = "." digit { digit } .
exp      = [ "e" | "E" ] [ "-" | "+" ] digit { digit } .
constant = "true" | "false" | "null" .
```

---

## 2. Quality Characteristics & Implementation

### Verification Structure
- **Self-Test Suite**: A built-in suite of 20+ test cases executed via `--selftest`.
- **Success Marker**: Upon completion of all tests, the program must output `JSONPARSE OK <count>` and exit with code 0.
- **Failure Handling**: Any mismatch between the parsed result and the expected Python object must result in a non-zero exit code and an error message detailing the failure.

### Strategy for Specific Challenges
- **Escape Sequences (`\uXXXX`)**:
    - When `\u` is encountered, the next 4 characters are read.
    - They are converted from hex to an integer using `int(hex_str, 16)`.
    - The character is appended using `chr()`.
- **Scientific Notation**:
    - The number parser identifies the optional `e` or `E`.
    - It extracts the sign and the exponent digits.
    - Python's `float()` constructor is used on the fully extracted numeric string (e.g., `"-1.23e-10"`) to ensure precision and correctness according to IEEE 754.
- **Whitespace**: 
    - A helper method `consume_whitespace()` will be called before parsing any significant token to ensure flexibility.

---

## 3. Design Rules

### General Rules
- **No `json` module**: The string `import json` or `from json` must not appear in the code.
- **Read-only input**: The parser must treat the input text as a read-only string.
- **No temporary files**: All processing must happen in memory.

### Output Rules
- **Success String**: Exact match: `JSONPARSE OK <number>` (e.g., `JSONPARSE OK 25`).
- **Exit Codes**: 0 for total success, non-zero for any test failure.

---

## 4. Test Case Suite (20+ Cases)

The following cases will be implemented in the `--selftest` logic:

| Category | Test Case (JSON Input) | Expected Python Result |
| :--- | :--- | :--- |
| **Empty/Basic** | `{}` | `{}` |
| | `[]` | `[]` |
| | `""` | `""` |
| | `null` | `None` |
| | `true` | `True` |
| | `false` | `False` |
| **Strings** | `"Hello World"` | `"Hello World"` |
| | `"Line\nBreak"` | `"Line\nBreak"` |
| | `"Quote \" test"` | `"Quote \" test"` |
| | `"Backslash \\ test"` | `"Backslash \\ test"` |
| | `"\u0041\u0042"` | `"AB"` |
| | `"\u2605"` | `"⭐"` |
| **Numbers** | `123` | `123` |
| | `-123` | `-123` |
| | `123.456` | `123.456` |
| | `-0.123` | `-0.123` |
| | `1.23e10` | `12300000000.0` |
| | `1.23E-10` | `1.23e-10` |
| | `-5.0e+2` | `-500.0` |
| **Collections** | `[1, 2, 3]` | `[1, 2, 3]` |
| | `{"a": 1, "b": 2}` | `{"a": 1, "b": 2}` |
| **Nested** | `{"a": [1, {"b": 2}, 3]}` | `{"a": [1, {"b": 2}, 3]}` |
| | `[[[1]]]` | `[[[1]]]` |
| **Mixed** | `{"k": [true, false, null, "s", 1.1]}` | `{"k": [True, False, None, "s", 1.1]}` |
