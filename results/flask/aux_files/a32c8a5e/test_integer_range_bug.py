#!/usr/bin/env python3
"""Test for potential bug in integer_range validator error message"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer_range

print("Testing integer_range validator with float bounds:")
print("-" * 50)

# Create a validator with float bounds
validator = integer_range(1.5, 10.5)

print(f"Created integer_range validator with bounds (1.5, 10.5)")
print("\nTesting value 0 (below range):")

try:
    result = validator(0)
    print(f"  ✓ Accepted: {result}")
except ValueError as e:
    print(f"  ✗ Rejected with error: {e}")
    print(f"\nBUG FOUND!")
    print(f"  The error message uses %d format which truncates floats.")
    print(f"  Expected: 'Integer must be between 1.5 and 10.5'")
    print(f"  Actual: '{e}'")
    print(f"  This misleads users about the actual bounds!")

print("\nTesting value 11 (above range):")
try:
    result = validator(11)
    print(f"  ✓ Accepted: {result}")
except ValueError as e:
    print(f"  ✗ Rejected with error: {e}")
    
print("\n" + "=" * 50)
print("Analysis:")
print("The integer_range function accepts float parameters but")
print("formats them as integers in error messages using %d.")
print("This causes incorrect error messages that mislead users.")