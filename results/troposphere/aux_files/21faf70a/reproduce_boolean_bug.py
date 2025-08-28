#!/usr/bin/env python3
"""Minimal reproduction of boolean validator bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test cases that should be accepted
print("Testing valid inputs:")
for value in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
    try:
        result = boolean(value)
        print(f"  boolean({value!r}) = {result!r}")
    except ValueError as e:
        print(f"  boolean({value!r}) raised ValueError: {e}")

# Test cases that should be rejected but aren't
print("\nTesting float inputs (should raise ValueError):")
for value in [0.0, 1.0, 0.5, -1.0, 2.0, 3.14]:
    try:
        result = boolean(value)
        print(f"  boolean({value!r}) = {result!r} (BUG: should raise ValueError)")
    except ValueError as e:
        print(f"  boolean({value!r}) raised ValueError: {e} (correct)")

# Let's check the implementation
print("\nLooking at the implementation:")
print("The boolean function uses 'in' operator to check membership")
print("0.0 in [False, 0, '0', 'false', 'False'] evaluates to:", 0.0 in [False, 0, "0", "false", "False"])
print("1.0 in [True, 1, '1', 'true', 'True'] evaluates to:", 1.0 in [True, 1, "1", "true", "True"])
print("\nThis is because in Python: 0.0 == 0 is", 0.0 == 0, "and 1.0 == 1 is", 1.0 == 1)