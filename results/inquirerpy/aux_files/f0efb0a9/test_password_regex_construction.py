"""Test the regex construction logic in PasswordValidator more thoroughly."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.validator import PasswordValidator
import re

print("Testing PasswordValidator regex pattern construction:\n")

# Test all combinations of constraints
test_cases = [
    # (length, cap, special, number, expected_pattern)
    (None, False, False, False, r'^.*$'),
    (5, False, False, False, r'^.{5,}$'),
    (None, True, False, False, r'^(?=.*[A-Z]).*$'),
    (None, False, True, False, r'^(?=.*[@$!%*#?&]).*$'),
    (None, False, False, True, r'^(?=.*[0-9]).*$'),
    (5, True, True, True, r'^(?=.*[A-Z])(?=.*[@$!%*#?&])(?=.*[0-9]).{5,}$'),
    (0, False, False, False, r'^.*$'),  # Special case: length=0
]

print("Expected regex patterns:")
for length, cap, special, number, expected in test_cases:
    validator = PasswordValidator(length=length, cap=cap, special=special, number=number)
    actual = validator._re.pattern
    status = "✓" if actual == expected else "✗"
    print(f"  {status} length={length}, cap={cap}, special={special}, number={number}")
    print(f"    Expected: {expected}")
    print(f"    Actual:   {actual}")
    if actual != expected:
        print(f"    MISMATCH!")
    print()

# Test that the special characters list is correct
print("\nTesting special characters definition:")
validator = PasswordValidator(special=True)
pattern = validator._re.pattern
print(f"  Pattern: {pattern}")

# Extract the special chars from the pattern
import re
match = re.search(r'\[\@\$\!\%\*\#\?\&\]|\[@\$!%\*#\?&\]', pattern)
if match:
    print(f"  Special chars in regex: {match.group()}")
    expected_chars = '@$!%*#?&'
    print(f"  Expected special chars: {expected_chars}")
    
    # Test each special char
    from unittest.mock import Mock
    for char in expected_chars:
        doc = Mock()
        doc.text = char
        doc.cursor_position = 1
        try:
            validator.validate(doc)
            print(f"    '{char}' - PASS")
        except:
            print(f"    '{char}' - FAIL (BUG!)")

# Test some complex real-world password patterns
print("\n\nTesting real-world password patterns:")
test_passwords = [
    ("P@ssw0rd", {"length": 8, "cap": True, "special": True, "number": True}, True),
    ("password", {"length": 8, "cap": True, "special": True, "number": True}, False),
    ("P@ssword", {"length": 8, "cap": True, "special": True, "number": True}, False),  # missing number
    ("P@ssw0r", {"length": 8, "cap": True, "special": True, "number": True}, False),   # too short
    ("", {"length": None, "cap": False, "special": False, "number": False}, True),     # empty allowed with no constraints
    ("A!1", {"length": 3, "cap": True, "special": True, "number": True}, True),        # minimum valid
]

for password, constraints, should_pass in test_passwords:
    validator = PasswordValidator(**constraints)
    doc = Mock()
    doc.text = password
    doc.cursor_position = len(password)
    
    try:
        validator.validate(doc)
        result = "PASS"
    except:
        result = "FAIL"
    
    expected = "PASS" if should_pass else "FAIL"
    status = "✓" if result == expected else "✗"
    
    print(f"  {status} '{password}' with {constraints}")
    print(f"    Expected: {expected}, Got: {result}")
    if result != expected:
        print(f"    UNEXPECTED RESULT!")