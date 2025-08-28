#!/usr/bin/env python3
"""Proposed fix for the boolean validator bug."""

# Current buggy implementation:
def boolean_buggy(x):
    if x in [True, 1, "1", "true", "True"]:
        return True
    if x in [False, 0, "0", "false", "False"]:
        return False
    raise ValueError

# Fixed implementation:
def boolean_fixed(x):
    # Check for exact boolean types first
    if x is True:
        return True
    if x is False:
        return False
    # Check for integer types (but not float)
    if isinstance(x, int) and not isinstance(x, bool):
        if x == 1:
            return True
        if x == 0:
            return False
    # Check for string types
    if isinstance(x, str):
        if x in ["1", "true", "True"]:
            return True
        if x in ["0", "false", "False"]:
            return False
    raise ValueError

# Test the fix
print("Testing fixed implementation:")
test_cases = [
    # Valid cases
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    ("1", True),
    ("0", False),
    ("true", True),
    ("false", False),
    ("True", True),
    ("False", False),
    # Invalid cases that should raise ValueError
    (0.0, ValueError),
    (1.0, ValueError),
    (0.5, ValueError),
    (2, ValueError),
    (-1, ValueError),
    ("yes", ValueError),
    ("no", ValueError),
    ([], ValueError),
    ({}, ValueError),
    (None, ValueError),
]

for value, expected in test_cases:
    try:
        result = boolean_fixed(value)
        if expected == ValueError:
            print(f"  boolean_fixed({value!r}) = {result!r} - FAIL: should raise ValueError")
        else:
            if result == expected:
                print(f"  boolean_fixed({value!r}) = {result!r} - PASS")
            else:
                print(f"  boolean_fixed({value!r}) = {result!r} - FAIL: expected {expected!r}")
    except ValueError:
        if expected == ValueError:
            print(f"  boolean_fixed({value!r}) raised ValueError - PASS")
        else:
            print(f"  boolean_fixed({value!r}) raised ValueError - FAIL: expected {expected!r}")