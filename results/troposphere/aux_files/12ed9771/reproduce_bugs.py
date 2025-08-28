#!/usr/bin/env python3
"""Reproduce the bugs found in troposphere validators."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, double
import math

print("Bug 1: integer validator crashes on infinity")
print("=" * 50)
try:
    result = integer(float('inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
except ValueError as e:
    print(f"ValueError: {e}")

print("\nTrying with negative infinity:")
try:
    result = integer(float('-inf'))
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
except ValueError as e:
    print(f"ValueError: {e}")

print("\n" + "=" * 50)
print("\nBug 2: double validator with NaN")
print("=" * 50)
try:
    nan_value = float('nan')
    result = double(nan_value)
    print(f"Input: {nan_value}")
    print(f"Result: {result}")
    print(f"Result == Input: {result == nan_value}")
    print(f"Result is NaN: {math.isnan(result)}")
    print(f"Input is NaN: {math.isnan(nan_value)}")
except ValueError as e:
    print(f"ValueError: {e}")

print("\nChecking if the issue is in the comparison:")
nan1 = float('nan')
nan2 = float('nan')
print(f"nan == nan: {nan1 == nan2}")
print(f"Note: NaN is never equal to anything, including itself!")

print("\n" + "=" * 50)
print("\nExpected behavior comparison:")
print("Python's int() with infinity:")
try:
    int(float('inf'))
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

print("\nPython's float() with NaN:")
nan = float('nan')
print(f"  float('nan') works: {nan}")
print(f"  But nan == nan is: {nan == nan}")