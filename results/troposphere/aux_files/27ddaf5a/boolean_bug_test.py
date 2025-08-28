#!/usr/bin/env python3
"""Test to verify boolean validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

print("Testing boolean validator behavior...")
print("="*50)

# First, let's understand Python's behavior
print("\nPython equality behavior:")
print(f"1 == True: {1 == True}")
print(f"0 == False: {0 == False}")
print(f"'1' == True: {'1' == True}")
print(f"'0' == False: {'0' == False}")

print("\nList membership checks:")
print(f"1 in [True]: {1 in [True]}")
print(f"True in [1]: {True in [1]}")
print(f"0 in [False]: {0 in [False]}")
print(f"False in [0]: {False in [0]}")

print("\n" + "="*50)
print("Testing boolean validator:")

# Test cases
test_cases = [
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
]

for input_val, expected in test_cases:
    try:
        result = boolean(input_val)
        status = "✓" if result == expected else "✗"
        print(f"{status} boolean({input_val!r:10}) = {result:5} (expected {expected})")
    except ValueError as e:
        print(f"✗ boolean({input_val!r:10}) raised ValueError")

print("\n" + "="*50)
print("Checking list membership order dependency:")

# The bug might be in the order of checking
def boolean_original(x):
    """Original implementation from troposphere"""
    if x in [True, 1, "1", "true", "True"]:
        return True
    if x in [False, 0, "0", "false", "False"]:
        return False
    raise ValueError

def boolean_fixed(x):
    """Fixed implementation with string checks first"""
    # Check strings first to avoid integer/boolean confusion
    if x in ["1", "true", "True"]:
        return True
    if x in ["0", "false", "False"]:
        return False
    if x in [True, 1]:
        return True
    if x in [False, 0]:
        return False
    raise ValueError

print("\nTesting edge case where order might matter:")

# Actually, since 1 == True and 0 == False in Python,
# the membership check will work correctly regardless of order
# Let's verify this:

test_list_true = [True, 1, "1", "true", "True"]
test_list_false = [False, 0, "0", "false", "False"]

print(f"\nChecking if 1 is in {test_list_true[:2]}:")
print(f"1 in [True, 1, ...]: {1 in test_list_true}")

print(f"\nChecking if True is in {test_list_true[:2]}:")
print(f"True in [True, 1, ...]: {True in test_list_true}")

# Let's check if there's any actual difference
print("\n" + "="*50)
print("Hypothesis: The validator works correctly due to Python's equality semantics")
print("1 == True and 0 == False, so membership checks work correctly")

# Let me verify there's no bug
print("\nVerifying no bug exists:")
assert boolean(1) == True
assert boolean(0) == False
assert boolean(True) == True
assert boolean(False) == False
print("✓ All basic tests pass")

# The real bug might be elsewhere...
print("\n" + "="*50)
print("Checking for potential issues with type preservation...")

# What if the issue is that the function returns True/False but we expect the original type?
print(f"\nboolean(1) is True: {boolean(1) is True}")
print(f"boolean(1) == True: {boolean(1) == True}")
print(f"type(boolean(1)): {type(boolean(1))}")

print(f"\nboolean(0) is False: {boolean(0) is False}")
print(f"boolean(0) == False: {boolean(0) == False}")
print(f"type(boolean(0)): {type(boolean(0))}")