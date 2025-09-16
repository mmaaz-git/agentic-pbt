#!/usr/bin/env python3
"""Reproduction script for Separator __str__ bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages")

from InquirerPy.separator import Separator

print("Bug Reproduction: Separator.__str__() violates Python's string contract")
print("=" * 60)

# Test case 1: None
print("\nTest 1: Separator with None")
try:
    separator = Separator(None)
    result = str(separator)  # This should raise TypeError
    print(f"  Result: {result!r} (type: {type(result).__name__})")
    print("  BUG: str() should not accept non-string return from __str__")
except TypeError as e:
    print(f"  Expected TypeError: {e}")

# Test case 2: Integer
print("\nTest 2: Separator with integer")
try:
    separator = Separator(42)
    result = str(separator)  # This should raise TypeError
    print(f"  Result: {result!r} (type: {type(result).__name__})")
    print("  BUG: str() should not accept non-string return from __str__")
except TypeError as e:
    print(f"  Expected TypeError: {e}")

# Test case 3: List
print("\nTest 3: Separator with list")
try:
    separator = Separator([1, 2, 3])
    result = str(separator)  # This should raise TypeError
    print(f"  Result: {result!r} (type: {type(result).__name__})")
    print("  BUG: str() should not accept non-string return from __str__")
except TypeError as e:
    print(f"  Expected TypeError: {e}")

# Test case 4: Boolean
print("\nTest 4: Separator with boolean")
try:
    separator = Separator(True)
    result = str(separator)  # This should raise TypeError
    print(f"  Result: {result!r} (type: {type(result).__name__})")
    print("  BUG: str() should not accept non-string return from __str__")
except TypeError as e:
    print(f"  Expected TypeError: {e}")

print("\n" + "=" * 60)
print("Summary: The __str__ method returns self._line without")
print("converting it to a string, violating Python's contract that")
print("__str__ must return a string object.")