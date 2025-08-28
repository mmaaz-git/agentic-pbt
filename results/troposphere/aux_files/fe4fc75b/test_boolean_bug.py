#!/usr/bin/env python3
"""Test for potential boolean validator bug with float values"""

import sys
import os

# Add the troposphere package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

print("Testing boolean validator with various numeric types...")
print("=" * 60)

# Test cases that should logically be True  
true_test_cases = [
    (True, "bool True"),
    (1, "int 1"),
    ("1", "str '1'"),
    ("true", "str 'true'"),
    ("True", "str 'True'"),
    (1.0, "float 1.0"),  # This might fail!
]

# Test cases that should logically be False
false_test_cases = [
    (False, "bool False"),
    (0, "int 0"),
    ("0", "str '0'"),
    ("false", "str 'false'"),
    ("False", "str 'False'"),
    (0.0, "float 0.0"),  # This might fail!
]

print("Testing TRUE-like values:")
for value, description in true_test_cases:
    try:
        result = validators.boolean(value)
        print(f"  ✓ boolean({description:<15}) = {result}")
        assert result is True, f"Expected True but got {result}"
    except ValueError as e:
        print(f"  ✗ boolean({description:<15}) raised ValueError")
        # This is a bug if value is 1.0
        if value == 1.0:
            print("    ^ BUG FOUND: float 1.0 should be accepted as True!")

print("\nTesting FALSE-like values:")
for value, description in false_test_cases:
    try:
        result = validators.boolean(value)
        print(f"  ✓ boolean({description:<15}) = {result}")
        assert result is False, f"Expected False but got {result}"
    except ValueError as e:
        print(f"  ✗ boolean({description:<15}) raised ValueError")
        # This is a bug if value is 0.0
        if value == 0.0:
            print("    ^ BUG FOUND: float 0.0 should be accepted as False!")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("The boolean validator uses 'in' operator with a list,")
print("which checks for identity/equality. Since 1.0 == 1 is True")
print("in Python but 1.0 is not in [True, 1, ...], it fails.")
print("This is inconsistent with Python's bool(1.0) which returns True.")

# Let's verify Python's behavior
print("\nPython's built-in bool() for comparison:")
print(f"  bool(1.0) = {bool(1.0)}")
print(f"  bool(0.0) = {bool(0.0)}")
print(f"  1.0 == 1 = {1.0 == 1}")
print(f"  0.0 == 0 = {0.0 == 0}")
print(f"  1.0 in [1] = {1.0 in [1]}")  # This is True!
print(f"  0.0 in [0] = {0.0 in [0]}")  # This is True!

print("\nWait, let me double-check the 'in' operator behavior...")
print(f"  1.0 in [True, 1, '1', 'true', 'True'] = {1.0 in [True, 1, '1', 'true', 'True']}")
print(f"  0.0 in [False, 0, '0', 'false', 'False'] = {0.0 in [False, 0, '0', 'false', 'False']}")

print("\nInteresting! The 'in' operator DOES match 1.0 with 1 and 0.0 with 0.")
print("So if there's a bug, it must be elsewhere...")

# Let's test with actual Pipeline code
print("\n" + "=" * 60)
print("Testing with actual Pipeline.Activate field...")

from troposphere import datapipeline

pipeline = datapipeline.Pipeline("TestPipeline")
pipeline.Name = "Test"

test_values = [True, 1, 1.0, "true", False, 0, 0.0, "false"]
for val in test_values:
    try:
        pipeline.Activate = val
        print(f"  Pipeline.Activate = {val:<10} -> stored as {pipeline.Activate}")
    except (TypeError, ValueError) as e:
        print(f"  Pipeline.Activate = {val:<10} -> ERROR: {e}")