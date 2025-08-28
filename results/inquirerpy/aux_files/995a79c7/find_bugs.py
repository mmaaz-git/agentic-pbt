#!/usr/bin/env python3
"""Direct bug finding in InquirerPy."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.validator import NumberValidator, PasswordValidator, EmptyInputValidator
from InquirerPy.resolver import _get_questions
from prompt_toolkit.validation import ValidationError
from InquirerPy.exceptions import InvalidArgument

class FakeDocument:
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)

print("=" * 60)
print("Bug Hunt in InquirerPy")
print("=" * 60)

bugs_found = []

# Test 1: NumberValidator with leading zeros
print("\n1. Testing NumberValidator with leading zeros...")
validator_int = NumberValidator(float_allowed=False)
test_cases = ["007", "000", "-000", "+000", "0000000"]

for test in test_cases:
    doc = FakeDocument(test)
    try:
        validator_int.validate(doc)
        # Check if Python would accept it
        try:
            int_val = int(test)
            print(f"  ✓ '{test}' -> {int_val} (consistent)")
        except ValueError:
            print(f"  ✗ BUG: '{test}' accepted by validator but not by Python int()")
            bugs_found.append(f"NumberValidator accepts '{test}' but Python int() doesn't")
    except ValidationError:
        # Check if Python would reject it too
        try:
            int_val = int(test)
            print(f"  ✗ BUG: '{test}' rejected by validator but accepted by Python int() as {int_val}")
            bugs_found.append(f"NumberValidator rejects '{test}' but Python int() accepts it")
        except ValueError:
            print(f"  ✓ '{test}' rejected (consistent)")

# Test 2: PasswordValidator with length=0
print("\n2. Testing PasswordValidator with length=0...")
validator_pwd = PasswordValidator(length=0)
test_passwords = ["", "a", "abc"]

for pwd in test_passwords:
    doc = FakeDocument(pwd)
    try:
        validator_pwd.validate(doc)
        print(f"  ✓ Password '{pwd}' accepted with length=0")
    except ValidationError:
        print(f"  ✗ BUG: Password '{pwd}' rejected with length=0")
        bugs_found.append(f"PasswordValidator(length=0) rejects '{pwd}'")

# Test 3: PasswordValidator regex construction edge case
print("\n3. Testing PasswordValidator regex edge cases...")

# Test with only length constraint
validator = PasswordValidator(length=3)
test_pwd = "ab"  # Too short
doc = FakeDocument(test_pwd)
try:
    validator.validate(doc)
    print(f"  ✗ BUG: Password 'ab' accepted with minimum length=3")
    bugs_found.append("PasswordValidator(length=3) accepts 2-char password 'ab'")
except ValidationError:
    print(f"  ✓ Password 'ab' correctly rejected with minimum length=3")

# Test with no constraints
validator = PasswordValidator()
test_pwd = ""
doc = FakeDocument(test_pwd)
try:
    validator.validate(doc)
    print(f"  ✓ Empty password accepted with no constraints")
except ValidationError:
    print(f"  ✗ BUG: Empty password rejected with no constraints")
    bugs_found.append("PasswordValidator() rejects empty password")

# Test 4: _get_questions with None
print("\n4. Testing _get_questions with edge cases...")
try:
    result = _get_questions(None)
    print(f"  ✗ BUG: _get_questions accepts None: {result}")
    bugs_found.append(f"_get_questions accepts None and returns {result}")
except (InvalidArgument, TypeError, AttributeError) as e:
    print(f"  ✓ _get_questions correctly rejects None")

# Test 5: NumberValidator with scientific notation
print("\n5. Testing NumberValidator with scientific notation...")
validator_float = NumberValidator(float_allowed=True)
sci_notation = ["1e5", "1E5", "1e-5", "1.23e10", "-4.56E-7"]

for test in sci_notation:
    doc = FakeDocument(test)
    try:
        validator_float.validate(doc)
        float_val = float(test)
        print(f"  ✓ '{test}' -> {float_val} accepted")
    except ValidationError:
        try:
            float_val = float(test)
            print(f"  ✗ BUG: '{test}' rejected but Python accepts as {float_val}")
            bugs_found.append(f"NumberValidator(float_allowed=True) rejects '{test}'")
        except ValueError:
            print(f"  ✓ '{test}' rejected (consistent)")

# Test 6: EmptyInputValidator boundary
print("\n6. Testing EmptyInputValidator edge cases...")
validator_empty = EmptyInputValidator()
edge_cases = ["", " ", "\t", "\n", "\r", "\0"]

for test in edge_cases:
    doc = FakeDocument(test)
    try:
        validator_empty.validate(doc)
        if len(test) > 0:
            print(f"  ✓ Non-empty '{repr(test)}' accepted")
        else:
            print(f"  ✗ BUG: Empty string accepted")
            bugs_found.append("EmptyInputValidator accepts empty string")
    except ValidationError:
        if len(test) == 0:
            print(f"  ✓ Empty string rejected")
        else:
            print(f"  ✗ BUG: Non-empty '{repr(test)}' rejected")
            bugs_found.append(f"EmptyInputValidator rejects non-empty '{repr(test)}'")

# Summary
print("\n" + "=" * 60)
print("Bug Hunt Summary")
print("=" * 60)

if bugs_found:
    print(f"\n✗ Found {len(bugs_found)} potential bug(s):")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("\n✓ No bugs found in the tested properties!")

print("\nBug hunt complete.")