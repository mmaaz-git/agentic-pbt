#!/usr/bin/env python3
"""Detailed analysis of PasswordValidator regex construction."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

print("Analyzing PasswordValidator regex patterns...")
print("=" * 60)

# Let's trace through the regex construction
def build_regex(length=None, cap=False, special=False, number=False):
    """Recreate the regex building logic from PasswordValidator."""
    password_pattern = r"^"
    if cap:
        password_pattern += r"(?=.*[A-Z])"
    if special:
        password_pattern += r"(?=.*[@$!%*#?&])"
    if number:
        password_pattern += r"(?=.*[0-9])"
    password_pattern += r"."
    if length:
        password_pattern += r"{%s,}" % length
    else:
        password_pattern += r"*"
    password_pattern += r"$"
    return password_pattern

# Test different constraint combinations
test_configs = [
    {"length": None, "cap": False, "special": False, "number": False},
    {"length": 0, "cap": False, "special": False, "number": False},
    {"length": 1, "cap": False, "special": False, "number": False},
    {"length": 5, "cap": True, "special": False, "number": False},
    {"length": None, "cap": True, "special": True, "number": True},
]

for config in test_configs:
    pattern = build_regex(**config)
    regex = re.compile(pattern)
    print(f"\nConfig: {config}")
    print(f"Pattern: {pattern}")
    
    # Test some strings
    test_strings = ["", "a", "A", "1", "@", "abc", "ABC123@", "short"]
    print("Test results:")
    for s in test_strings:
        match = regex.match(s)
        print(f"  '{s}': {'MATCH' if match else 'NO MATCH'}")

# Specific bug investigation: length=0
print("\n" + "-" * 60)
print("BUG INVESTIGATION: PasswordValidator with length=0")
print("-" * 60)

from InquirerPy.validator import PasswordValidator
from prompt_toolkit.validation import ValidationError

class FakeDocument:
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)

# Create validator with length=0
validator = PasswordValidator(length=0)
print(f"Created PasswordValidator(length=0)")

# Check the actual regex pattern
print(f"Regex pattern: {validator._re.pattern}")

# Test empty string
doc = FakeDocument("")
print("\nTesting empty string '':")
try:
    validator.validate(doc)
    print("  Result: ACCEPTED")
except ValidationError as e:
    print(f"  Result: REJECTED - {e.message}")

# The regex with length=0 becomes: ^.{0,}$
# This should match any string including empty!
# Let's verify this understanding
test_regex = re.compile(r"^.{0,}$")
print(f"\nDirect regex test with pattern '^.{{0,}}$':")
print(f"  Empty string: {bool(test_regex.match(''))}")
print(f"  'a': {bool(test_regex.match('a'))}")
print(f"  'abc': {bool(test_regex.match('abc'))}")

# However, let's check what the actual constructed pattern is
print(f"\nActual validator regex: {validator._re.pattern}")
print(f"Expected pattern: ^.{{0,}}$")

# Direct test of the regex
print("\nDirect test of validator's regex:")
for test in ["", "a", "abc"]:
    match = validator._re.match(test)
    print(f"  '{test}': {'MATCH' if match else 'NO MATCH'}")