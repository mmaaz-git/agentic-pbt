#!/usr/bin/env python3
"""Verify the PasswordValidator length=0 bug."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.validator import PasswordValidator
from prompt_toolkit.validation import ValidationError

class FakeDocument:
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)

print("=" * 60)
print("BUG VERIFICATION: PasswordValidator with length=0")
print("=" * 60)

# The bug hypothesis:
# When length=0 is passed, the code uses `if length:` which evaluates to False
# This causes it to use the same regex as length=None (no length constraint)
# However, the user's intent with length=0 is different from length=None

print("\n1. Testing PasswordValidator(length=0)...")
validator_zero = PasswordValidator(length=0)
print(f"   Regex pattern: {validator_zero._re.pattern}")

print("\n2. Testing PasswordValidator(length=None)...")
validator_none = PasswordValidator(length=None)
print(f"   Regex pattern: {validator_none._re.pattern}")

print("\n3. Testing PasswordValidator(length=1)...")
validator_one = PasswordValidator(length=1)
print(f"   Regex pattern: {validator_one._re.pattern}")

# The patterns should be different but they're the same!
if validator_zero._re.pattern == validator_none._re.pattern:
    print("\n✗ BUG CONFIRMED: length=0 produces same regex as length=None")
    print(f"   Both produce: {validator_zero._re.pattern}")
    print(f"   Expected for length=0: ^.{{0,}}$ (which is the same as ^.*$)")
    print(f"   This means length=0 doesn't work as intended!")
else:
    print("\n✓ No bug: length=0 produces different regex from length=None")

# Let's also verify the actual behavior
print("\n4. Behavior verification:")

# With length=0, we'd expect to accept any length including empty
# With length=None, we'd also expect to accept any length
# But the semantic meaning is different - length=0 explicitly sets minimum to 0

print("\nExpected behavior:")
print("  length=0: Explicitly set minimum length to 0 (accept everything)")
print("  length=None: No length constraint specified (accept everything)")
print("  length=1: Minimum length of 1 (reject empty)")

print("\nActual behavior with empty password '':")
for length_val, validator in [(0, validator_zero), (None, validator_none), (1, validator_one)]:
    doc = FakeDocument("")
    try:
        validator.validate(doc)
        print(f"  length={length_val}: ACCEPTED")
    except ValidationError:
        print(f"  length={length_val}: REJECTED")

print("\nActual behavior with password 'a':")
for length_val, validator in [(0, validator_zero), (None, validator_none), (1, validator_one)]:
    doc = FakeDocument("a")
    try:
        validator.validate(doc)
        print(f"  length={length_val}: ACCEPTED")
    except ValidationError:
        print(f"  length={length_val}: REJECTED")

# The real issue: What if someone combines length=0 with other constraints?
print("\n5. Combined constraints test:")
print("Testing PasswordValidator(length=0, cap=True)...")
validator_combo = PasswordValidator(length=0, cap=True)
print(f"   Regex pattern: {validator_combo._re.pattern}")

# This should require a capital letter but allow empty string? Or not?
# The semantic is unclear, but the code doesn't handle it properly

print("\nThe core issue:")
print("  The code uses 'if length:' which treats length=0 as False")
print("  This makes length=0 behave identically to length=None")
print("  The fix would be to use 'if length is not None:' instead")