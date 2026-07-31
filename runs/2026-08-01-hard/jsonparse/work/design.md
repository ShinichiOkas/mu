# Design Document: Recursive Descent JSON Parser

## 1. Structure

### 1.1 File Configuration
The implementation will consist of a single module `json_parser.py` containing the following components:
- `Lexer`: Converts the input string into a stream of tokens.
- `Parser`: Consumes tokens and builds the Python object hierarchy using recursive descent.
- `JSONParser` (Main Class): Orchestrates the lexing and parsing process.

### 1.2 Data Flow
`Input String` $\rightarrow$ `Lexer (Token Stream)` $\rightarrow$ `Parser (Recursive Descent)` $\rightarrow$ `Python Object`

### 1.3 Responsibilities
- **Lexer**: 
    - Handle whitespace skipping.
    - Identify token types (Braces, Brackets, Colons, Commas, Strings, Numbers, Booleans, Null).
    - Handle escape sequences in strings.
    - Recognize scientific notation in numbers.
- **Parser**:
    - Validate JSON grammar.
    - Recursive calls for nested structures (Objects $\rightarrow$ Values $\rightarrow$ Objects).
    - Map JSON types to Python types.

## 2. Quality Characteristics and Verification

### 2.1 Verification Strategy
To ensure the parser is functioning correctly and to avoid "false positives" (where a script exits with 0 without actually testing anything), the implementation must include a self-test suite.

### 2.2 Validation Markers
The self-test output must print the following ASCII marker upon successful completion of all test cases:
- `[TEST_RESULT: PASS_ALL]`
- Each test case must print its status in the format: `Test Case <ID>: <PASS/FAIL>`

## 3. Design Rules

### 3.1 General Rules
- **Input files are read-only**: The parser must not modify, overwrite, or delete any input JSON files provided for parsing.
- **No temporary files**: Only the specified output files/objects should be created. Do not leave `.tmp` or `.log` files in the working directory.
- **Error Handling**: On parsing failure, the parser must raise a descriptive `JSONDecodeError` indicating the position of the error.

### 3.2 Tokenization Strategy
- **Strings**: Support double quotes. Handle escapes: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\uXXXX`.
- **Numbers**: 
    - Integer: `[-]digit{1,}`
    - Fraction: `[-]digit{1,}.digit{0,}`
    - Exponent: `[eE][+-]?digit{1,}`
- **Constants**: `true`, `false`, `null`.

### 3.3 Recursive Descent Logic
- `parse_value()`: Dispatches to `parse_object()`, `parse_array()`, `parse_string()`, `parse_number()`, or `parse_constant()` based on the current token.
- `parse_object()`: Consumes `{`, then pairs of `string : value` separated by commas, then `}`.
- `parse_array()`: Consumes `[`, then a list of `value` separated by commas, then `]`.

### 3.4 JSON Type Mapping
The following mapping must be strictly followed:

| JSON Type | Python Type | Note |
| :--- | :--- | :--- |
| Object | `dict` | Keys must be strings |
| Array | `list` | |
| String | `str` | Unicode |
| Number (Integer) | `int` | |
| Number (Float) | `float` | Including scientific notation |
| Boolean (true) | `True` | |
| Boolean (false) | `False` | |
| Null | `None` | |
