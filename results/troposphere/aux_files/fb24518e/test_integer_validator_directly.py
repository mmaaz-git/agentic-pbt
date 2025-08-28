#!/usr/bin/env python3
"""
Direct test of the integer validator bug.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, positive_integer

# Test the integer validator directly
print("Testing integer validator:")
result1 = integer(42.0)
print(f"integer(42.0) = {result1} (type: {type(result1).__name__})")
assert result1 == 42.0  # Bug: returns float unchanged
assert isinstance(result1, float)  # Bug: should be int

result2 = integer(42)
print(f"integer(42) = {result2} (type: {type(result2).__name__})")
assert result2 == 42
assert isinstance(result2, int)

# Test positive_integer validator
print("\nTesting positive_integer validator:")
result3 = positive_integer(42.0)
print(f"positive_integer(42.0) = {result3} (type: {type(result3).__name__})")
assert result3 == 42.0  # Same bug: returns float unchanged
assert isinstance(result3, float)  # Bug: should be int

print("\nBug confirmed: integer and positive_integer validators don't convert floats to ints")