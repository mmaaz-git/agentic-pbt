"""Further investigation of negative length behavior."""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

# Test Python's regex behavior with negative values
print("Python regex behavior with negative repetition counts:")

patterns = [
    r'.{-5,}',
    r'.{0,}',
    r'.{5,}',
]

test_strings = ['', 'a', 'abc', '12345', '123456789']

for pattern in patterns:
    print(f"\nPattern: {pattern}")
    try:
        regex = re.compile(pattern)
        print("  Compilation: SUCCESS")
        for s in test_strings:
            match = regex.match(s)
            print(f"    '{s}' -> {'MATCH' if match else 'NO MATCH'}")
    except re.error as e:
        print(f"  Compilation: FAILED - {e}")

# Now test what actually happens in PasswordValidator
print("\n" + "="*50)
print("PasswordValidator behavior:")

from unittest.mock import Mock
from InquirerPy.validator import PasswordValidator

def test_length(length_val):
    print(f"\nTesting length={length_val}")
    try:
        validator = PasswordValidator(length=length_val)
        print(f"  Pattern: {validator._re.pattern}")
        
        doc = Mock()
        for test_str in ['', 'a', 'abc', '12345', '123456789']:
            doc.text = test_str
            doc.cursor_position = len(test_str)
            try:
                validator.validate(doc)
                result = "PASS"
            except:
                result = "FAIL"
            print(f"    '{test_str}' -> {result}")
    except Exception as e:
        print(f"  Error creating validator: {e}")

test_length(-5)
test_length(0)
test_length(5)