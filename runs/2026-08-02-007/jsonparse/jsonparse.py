import sys

def parse(text):
    parser = JSONParser(text)
    result = parser.parse_value()
    parser.consume_whitespace()
    if parser.pos < len(text):
        raise ValueError(f"Unexpected characters at position {parser.pos}")
    return result

class JSONParser:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def consume_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def read_char(self):
        char = self.peek()
        if char:
            self.pos += 1
        return char

    def parse_value(self):
        self.consume_whitespace()
        char = self.peek()
        if char is None:
            raise ValueError("Unexpected end of input")
        
        if char == '{':
            return self.parse_object()
        elif char == '[':
            return self.parse_array()
        elif char == '"':
            return self.parse_string()
        elif char == '-' or ('0' <= char <= '9'):
            return self.parse_number()
        elif char == 't':
            return self.parse_constant("true", True)
        elif char == 'f':
            return self.parse_constant("false", False)
        elif char == 'n':
            return self.parse_constant("null", None)
        else:
            raise ValueError(f"Unexpected character '{char}' at position {self.pos}")

    def parse_object(self):
        self.read_char()  # Consume '{'
        self.consume_whitespace()
        obj = {}
        if self.peek() == '}':
            self.read_char()
            return obj
        
        while True:
            self.consume_whitespace()
            if self.peek() != '"':
                raise ValueError(f"Expected string key at position {self.pos}")
            key = self.parse_string()
            
            self.consume_whitespace()
            if self.read_char() != ':':
                raise ValueError(f"Expected ':' after key at position {self.pos}")
            
            val = self.parse_value()
            obj[key] = val
            
            self.consume_whitespace()
            char = self.read_char()
            if char == '}':
                return obj
            elif char != ',':
                raise ValueError(f"Expected ',' or '}}' at position {self.pos}")

    def parse_array(self):
        self.read_char()  # Consume '['
        self.consume_whitespace()
        arr = []
        if self.peek() == ']':
            self.read_char()
            return arr
        
        while True:
            val = self.parse_value()
            arr.append(val)
            
            self.consume_whitespace()
            char = self.read_char()
            if char == ']':
                return arr
            elif char != ',':
                raise ValueError(f"Expected ',' or ']' at position {self.pos}")

    def parse_string(self):
        self.read_char()  # Consume opening '"'
        result = []
        while True:
            char = self.read_char()
            if char is None:
                raise ValueError("Unterminated string")
            if char == '"':
                break
            if char == '\\':
                esc = self.read_char()
                if esc is None:
                    raise ValueError("Unterminated escape sequence")
                if esc == '"': result.append('"')
                elif esc == '\\': result.append('\\')
                elif esc == '/': result.append('/')
                elif esc == 'b': result.append('\b')
                elif esc == 'f': result.append('\f')
                elif esc == 'n': result.append('\n')
                elif esc == 'r': result.append('\r')
                elif esc == 't': result.append('\t')
                elif esc == 'u':
                    hex_str = ""
                    for _ in range(4):
                        h = self.read_char()
                        if h is None: raise ValueError("Unterminated unicode escape")
                        hex_str += h
                    result.append(chr(int(hex_str, 16)))
                else:
                    raise ValueError(f"Invalid escape sequence \\{esc}")
            else:
                result.append(char)
        return "".join(result)

    def parse_number(self):
        start = self.pos
        if self.peek() == '-':
            self.read_char()
        
        while self.peek() and ('0' <= self.peek() <= '9'):
            self.read_char()
            
        if self.peek() == '.':
            self.read_char()
            while self.peek() and ('0' <= self.peek() <= '9'):
                self.read_char()
                
        if self.peek() in ('e', 'E'):
            self.read_char()
            if self.peek() in ('-', '+'):
                self.read_char()
            while self.peek() and ('0' <= self.peek() <= '9'):
                self.read_char()
        
        num_str = self.text[start:self.pos]
        if '.' in num_str or 'e' in num_str or 'E' in num_str:
            return float(num_str)
        else:
            return int(num_str)

    def parse_constant(self, expected, value):
        for char in expected:
            if self.read_char() != char:
                raise ValueError(f"Expected {expected} at position {self.pos}")
        return value

def run_selftests():
    tests = [
        ("{}", {}),
        ("[]", []),
        ("\"\"", ""),
        ("null", None),
        ("true", True),
        ("false", False),
        ("\"Hello World\"", "Hello World"),
        ("\"Line\\nBreak\"", "Line\nBreak"),
        ("\"Quote \\\" test\"", "Quote \" test"),
        ("\"Backslash \\\\ test\"", "Backslash \\ test"),
        ("\"\\u0041\\u0042\"", "AB"),
        ("\"\\u2605\"", "\u2605"),
        ("123", 123),
        ("-123", -123),
        ("123.456", 123.456),
        ("-0.123", -0.123),
        ("1.23e10", 1.23e10),
        ("-1.23e-10", -1.23e-10),
        ("{\"a\": 1, \"b\": [1, 2, 3], \"c\": {\"d\": true}}", {"a": 1, "b": [1, 2, 3], "c": {"d": True}}),
        ("[1, \"two\", null, false]", [1, "two", None, False]),
        ("{\"key\": \"val\\u0020ue\"}", {"key": "val ue"}),
        ("  \"  spaces  \"  ", "  spaces  "),
        ("{\"nested\": [{\"a\": 1}, {\"b\": 2}]}", {"nested": [{"a": 1}, {"b": 2}]}),
    ]
    
    passed = 0
    for json_input, expected in tests:
        try:
            result = parse(json_input)
            if result == expected:
                passed += 1
            else:
                sys.stderr.write(f"Test Failed: Input {json_input}, Expected {expected}, Got {result}\n")
                sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Test Error: Input {json_input}, Error {e}\n")
            sys.exit(1)
            
    print(f"JSONPARSE OK {passed}")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        run_selftests()
    else:
        # Standard input parsing for general use
        try:
            input_text = sys.stdin.read()
            if input_text:
                print(parse(input_text))
        except EOFError:
            pass
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
