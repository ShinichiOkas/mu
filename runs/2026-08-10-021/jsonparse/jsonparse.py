import sys

def parse(text):
    """
    Parse a JSON string into corresponding Python types.
    Supported types: dict, list, str, int, float, bool, None.
    """
    pos = 0
    length = len(text)

    def skip_whitespace():
        nonlocal pos
        while pos < length and text[pos] in ' \n\r\t':
            pos += 1

    def parse_string():
        nonlocal pos
        pos += 1 # skip opening quote "
        result = []
        while pos < length:
            char = text[pos]
            pos += 1
            if char == '"':
                return "".join(result)
            elif char == '\\':
                if pos >= length:
                    raise ValueError("Unterminated escape sequence")
                esc = text[pos]
                pos += 1
                if esc == '"': result.append('"')
                elif esc == '\\': result.append('\\')
                elif esc == '/': result.append('/')
                elif esc == 'b': result.append('\b')
                elif esc == 'f': result.append('\f')
                elif esc == 'n': result.append('\n')
                elif esc == 'r': result.append('\r')
                elif esc == 't': result.append('\t')
                elif esc == 'u':
                    if pos + 3 >= length:
                        raise ValueError("Unterminated unicode escape")
                    hex_val = text[pos:pos+4]
                    result.append(chr(int(hex_val, 16)))
                    pos += 4
                else:
                    raise ValueError(f"Invalid escape sequence \\{esc}")
            else:
                result.append(char)
        raise ValueError("Unterminated string")

    def parse_number():
        nonlocal pos
        start = pos
        if text[pos] == '-':
            pos += 1
        if pos < length and text[pos] == '0':
            pos += 1
        elif pos < length and '1' <= text[pos] <= '9':
            while pos < length and '0' <= text[pos] <= '9':
                pos += 1
        else:
            raise ValueError("Invalid number format")
        if pos < length and text[pos] == '.':
            pos += 1
            if pos >= length or not ('0' <= text[pos] <= '9'):
                raise ValueError("Invalid fractional part")
            while pos < length and '0' <= text[pos] <= '9':
                pos += 1
        if pos < length and (text[pos] == 'e' or text[pos] == 'E'):
            pos += 1
            if pos < length and (text[pos] == '+' or text[pos] == '-'):
                pos += 1
            if pos >= length or not ('0' <= text[pos] <= '9'):
                raise ValueError("Invalid exponent part")
            while pos < length and '0' <= text[pos] <= '9':
                pos += 1
        num_str = text[start:pos]
        if '.' in num_str or 'e' in num_str or 'E' in num_str:
            return float(num_str)
        return int(num_str)

    def parse_array():
        nonlocal pos
        pos += 1 # skip [
        result = []
        skip_whitespace()
        if pos < length and text[pos] == ']':
            pos += 1
            return result
        while True:
            result.append(parse_value())
            skip_whitespace()
            if pos < length and text[pos] == ']':
                pos += 1
                return result
            if pos >= length or text[pos] != ',':
                raise ValueError("Expected , or ] in array")
            pos += 1
            skip_whitespace()

    def parse_object():
        nonlocal pos
        pos += 1 # skip {
        result = {}
        skip_whitespace()
        if pos < length and text[pos] == '}':
            pos += 1
            return result
        while True:
            skip_whitespace()
            if pos >= length or text[pos] != '"':
                raise ValueError("Expected string key in object")
            key = parse_string()
            skip_whitespace()
            if pos >= length or text[pos] != ':':
                raise ValueError("Expected : after key in object")
            pos += 1
            value = parse_value()
            result[key] = value
            skip_whitespace()
            if pos < length and text[pos] == '}':
                pos += 1
                return result
            if pos >= length or text[pos] != ',':
                raise ValueError("Expected , or } in object")
            pos += 1

    def parse_value():
        nonlocal pos
        skip_whitespace()
        if pos >= length:
            raise ValueError("Unexpected end of input")
        char = text[pos]
        if char == '{': return parse_object()
        if char == '[': return parse_array()
        if char == '"': return parse_string()
        if char == '-' or ('0' <= char <= '9'): return parse_number()
        if text.startswith('true', pos):
            pos += 4
            return True
        if text.startswith('false', pos):
            pos += 5
            return False
        if text.startswith('null', pos):
            pos += 4
            return None
        raise ValueError(f"Unexpected character {char} at position {pos}")

    result = parse_value()
    skip_whitespace()
    if pos < length:
        raise ValueError(f"Trailing data at position {pos}")
    return result

def run_selftests():
    tests = [
        ('null', None),
        ('true', True),
        ('false', False),
        ('""', ""),
        ('"hello"', "hello"),
        ('"hello world"', "hello world"),
        ('"\\""', '"'),
        ('"\\\\"', '\\'),
        ('"\\n"', '\n'),
        ('"\\u0041"', 'A'),
        ('"\\u0048\\u0065\\u006c\\u006c\\u006f"', 'Hello'),
        ('0', 0),
        ('123', 123),
        ('-123', -123),
        ('1.23', 1.23),
        ('-1.23', -1.23),
        ('1.2e3', 1200.0),
        ('-1.2E-2', -0.012),
        ('[]', []),
        ('[1, 2, 3]', [1, 2, 3]),
        ('[1, "two", true, null]', [1, "two", True, None]),
        ('[[1, 2], [3, 4]]', [[1, 2], [3, 4]]),
        ('{}', {}),
        ('{"key": "value"}', {"key": "value"}),
        ('{"a": 1, "b": 2}', {"a": 1, "b": 2}),
        ('{"a": [1, 2], "b": {"c": 3}}', {"a": [1, 2], "b": {"c": 3}}),
        ('[{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]', [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]),
        ('{"mixed": [1, {"inner": true}, null]}', {"mixed": [1, {"inner": True}, None]}),
        ('"\\u0020"', ' '),
    ]
    passed = 0
    for i, (input_str, expected) in enumerate(tests):
        try:
            actual = parse(input_str)
            if actual == expected:
                passed += 1
            else:
                print(f"Test {i} failed: input={input_str}, expected={expected}, actual={actual}")
        except Exception as e:
            print(f"Test {i} crashed: input={input_str}, error={e}")
    if passed == len(tests):
        print(f"JSONPARSE OK {passed}")
        sys.exit(0)
    else:
        print(f"Failed {len(tests) - passed} tests.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        run_selftests()
    else:
        if len(sys.argv) > 1:
            try:
                print(parse(sys.argv[1]))
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Usage: python jsonparse.py <json_string> or python jsonparse.py --selftest")
