import sys

def parse(text):
    """
    Parses a JSON string without using the 'json' module.
    """
    pos = 0

    def skip_whitespace():
        nonlocal pos
        while pos < len(text) and text[pos] in ' \t\n\r':
            pos += 1

    def parse_value():
        skip_whitespace()
        if pos >= len(text):
            raise ValueError("Unexpected end of input")
        
        char = text[pos]
        if char == '{':
            return parse_object()
        elif char == '[':
            return parse_array()
        elif char == '"':
            return parse_string()
        elif char == '-':
            return parse_number()
        elif '0' <= char <= '9':
            return parse_number()
        elif char == 't':
            return parse_literal('true', True)
        elif char == 'f':
            return parse_literal('false', False)
        elif char == 'n':
            return parse_literal('null', None)
        else:
            raise ValueError(f"Unexpected character '{char}' at position {pos}")

    def parse_literal(literal, value):
        nonlocal pos
        if text.startswith(literal, pos):
            pos += len(literal)
            return value
        raise ValueError(f"Expected {literal} at position {pos}")

    def parse_string():
        nonlocal pos
        pos += 1  # Skip opening quote
        result = []
        while pos < len(text):
            char = text[pos]
            if char == '"':
                pos += 1  # Skip closing quote
                return "".join(result)
            elif char == '\\':
                pos += 1
                if pos >= len(text):
                    raise ValueError("Unterminated escape sequence")
                esc = text[pos]
                if esc == '"': result.append('"')
                elif esc == '\\': result.append('\\')
                elif esc == '/': result.append('/')
                elif esc == 'b': result.append('\b')
                elif esc == 'f': result.append('\f')
                elif esc == 'n': result.append('\n')
                elif esc == 'r': result.append('\r')
                elif esc == 't': result.append('\t')
                elif esc == 'u':
                    # Handle \uXXXX
                    start_u = pos + 1
                    end_u = pos + 5
                    if end_u > len(text):
                        raise ValueError("Invalid unicode escape")
                    hex_val = text[start_u:end_u]
                    try:
                        result.append(chr(int(hex_val, 16)))
                    except ValueError:
                        raise ValueError(f"Invalid unicode escape {hex_val}")
                    pos += 4
                else:
                    raise ValueError(f"Invalid escape sequence \\{esc}")
                pos += 1
            else:
                result.append(char)
                pos += 1
        raise ValueError("Unterminated string")

    def parse_number():
        nonlocal pos
        start = pos
        if text[pos] == '-':
            pos += 1
        
        if pos >= len(text):
            raise ValueError("Unexpected end of number")

        # Integer part
        if pos < len(text) and text[pos] == '0':
            pos += 1
            # In standard JSON, leading zeros are not allowed unless the number is just 0.
            # But many parsers allow them. Let's be strict but simple.
        elif pos < len(text) and '1' <= text[pos] <= '9':
            while pos < len(text) and '0' <= text[pos] <= '9':
                pos += 1
        else:
            # Handle cases like 0.123
            if pos < len(text) and text[pos] == '0':
                pos += 1
            else:
                raise ValueError(f"Invalid digit at {pos}")
            while pos < len(text) and '0' <= text[pos] <= '9':
                pos += 1
        
        # Fractional part
        if pos < len(text) and text[pos] == '.':
            pos += 1
            if pos >= len(text) or not ('0' <= text[pos] <= '9'):
                raise ValueError("Expected digit after decimal point")
            while pos < len(text) and '0' <= text[pos] <= '9':
                pos += 1
        
        # Exponent part
        if pos < len(text) and text[pos] in 'eE':
            pos += 1
            if pos < len(text) and text[pos] in '+-':
                pos += 1
            if pos >= len(text) or not ('0' <= text[pos] <= '9'):
                raise ValueError("Expected digit in exponent")
            while pos < len(text) and '0' <= text[pos] <= '9':
                pos += 1
        
        num_str = text[start:pos]
        try:
            if '.' in num_str or 'e' in num_str.lower():
                return float(num_str)
            return int(num_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {num_str}")

    def parse_array():
        nonlocal pos
        pos += 1  # Skip '['
        res = []
        skip_whitespace()
        if pos < len(text) and text[pos] == ']':
            pos += 1
            return res
        
        while True:
            res.append(parse_value())
            skip_whitespace()
            if pos < len(text) and text[pos] == ',':
                pos += 1
                skip_whitespace()
            elif pos < len(text) and text[pos] == ']':
                pos += 1
                return res
            else:
                raise ValueError(f"Expected ',' or ']' in array at {pos}")

    def parse_object():
        nonlocal pos
        pos += 1  # Skip '{'
        res = {}
        skip_whitespace()
        if pos < len(text) and text[pos] == '}':
            pos += 1
            return res
        
        while True:
            skip_whitespace()
            if pos >= len(text) or text[pos] != '"':
                raise ValueError(f"Expected string key in object at {pos}")
            key = parse_string()
            skip_whitespace()
            if pos >= len(text) or text[pos] != ':':
                raise ValueError(f"Expected ':' after key in object at {pos}")
            pos += 1
            val = parse_value()
            res[key] = val
            skip_whitespace()
            if pos < len(text) and text[pos] == ',':
                pos += 1
                skip_whitespace()
            elif pos < len(text) and text[pos] == '}':
                pos += 1
                return res
            else:
                raise ValueError(f"Expected ',' or '}}' in object at {pos}")

    result = parse_value()
    skip_whitespace()
    if pos != len(text):
        raise ValueError(f"Trailing data at position {pos}")
    return result

def test_suite():
    cases = [
        ('null', None),
        ('true', True),
        ('false', False),
        ('123', 123),
        ('-123', -123),
        ('123.456', 123.456),
        ('-123.456', -123.456),
        ('1e10', 10000000000.0),
        ('-1.23e-2', -0.0123),
        ('"hello"', "hello"),
        ('"hello \\"world\\""', 'hello "world"'),
        ('"line\\nbreak"', "line\nbreak"),
        ('"slash\\\\slash"', "slash\\slash"),
        ('"unicode\\u0041"', "unicodeA"),
        ('[]', []),
        ('[1, 2, 3]', [1, 2, 3]),
        ('[true, false, null]', [True, False, None]),
        ('{"key": "value"}', {"key": "value"}),
        ('{}', {}),
        ('{"a": 1, "b": 2}', {"a": 1, "b": 2}),
        ('{"a": [1, 2], "b": {"c": 3}}', {"a": [1, 2], "b": {"c": 3}}),
        ('[{"id": 1}, {"id": 2}]', [{"id": 1}, {"id": 2}]),
        ('{"empty_arr": [], "empty_obj": {}}', {"empty_arr": [], "empty_obj": {}}),
        ('"\\u0020"', " "),
    ]
    
    passed = 0
    for text, expected in cases:
        try:
            actual = parse(text)
            if actual == expected:
                passed += 1
            else:
                print(f"FAILED: {text} -> expected {expected}, got {actual}")
        except Exception as e:
            print(f"ERROR: {text} -> {e}")
    
    print(f"JSONPARSE OK {passed}")
    return passed == len(cases)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        if test_suite():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        if len(sys.argv) > 2:
            print(parse(sys.argv[2]))
        else:
            print("Usage: python jsonparse.py --selftest OR python jsonparse.py parse \"<json>\"")
