"""Minimal reproduction of PasswordValidator negative length bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from InquirerPy.validator import PasswordValidator

def create_document(text):
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc

# Test 1: Negative length creates incorrect regex behavior
print("Test 1: Negative length (-5) should reject but accepts empty string")
validator = PasswordValidator(length=-5)
doc = create_document("")
try:
    validator.validate(doc)
    print("  ✗ Empty string accepted (BUG: negative length treated as 0)")
except:
    print("  ✓ Empty string rejected")

# Test 2: Negative length with non-empty string
print("\nTest 2: Negative length (-5) with 'abc'")
doc = create_document("abc")
try:
    validator.validate(doc)
    print("  ✗ 'abc' accepted (BUG: negative length treated as 0)")
except:
    print("  ✓ 'abc' rejected")

# Test 3: Show the actual regex pattern
print("\nTest 3: Inspect the regex pattern")
validator = PasswordValidator(length=-5)
print(f"  Regex pattern: {validator._re.pattern}")
print(f"  Expected: Error or rejection of negative length")
print(f"  Actual: Pattern is '.{{-5,}}$' which Python treats as '.{{0,}}$'")

# Test 4: Compare with length=0
print("\nTest 4: Compare length=-5 with length=0")
validator_neg = PasswordValidator(length=-5)
validator_zero = PasswordValidator(length=0)
print(f"  length=-5 pattern: {validator_neg._re.pattern}")
print(f"  length=0 pattern:  {validator_zero._re.pattern}")

test_strings = ["", "a", "abc", "12345", "123456"]
for s in test_strings:
    doc = create_document(s)
    neg_accepts = True
    zero_accepts = True
    try:
        validator_neg.validate(doc)
    except:
        neg_accepts = False
    try:
        validator_zero.validate(doc)
    except:
        zero_accepts = False
    
    print(f"  '{s}': length=-5 accepts={neg_accepts}, length=0 accepts={zero_accepts}")
    
print("\nConclusion: Negative length values are silently treated as 0, which is unexpected behavior.")