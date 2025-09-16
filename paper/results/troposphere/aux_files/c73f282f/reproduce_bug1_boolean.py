#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Reproduce boolean validator bug with float values"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Bug: boolean validator accepts float values like 0.0 and 1.0
# These should raise ValueError but don't

print("Testing boolean validator with float values:")

# Test case 1: 0.0 should not be accepted as False
try:
    result = boolean(0.0)
    print(f"boolean(0.0) = {result} (type: {type(result).__name__})")
    print("BUG: Float 0.0 was accepted as a boolean value!")
except ValueError:
    print("0.0 correctly rejected")

# Test case 2: 1.0 should not be accepted as True  
try:
    result = boolean(1.0)
    print(f"boolean(1.0) = {result} (type: {type(result).__name__})")
    print("BUG: Float 1.0 was accepted as a boolean value!")
except ValueError:
    print("1.0 correctly rejected")

# Test case 3: Other floats should also be rejected
try:
    result = boolean(2.0)
    print(f"boolean(2.0) = {result} (type: {type(result).__name__})")
    print("BUG: Float 2.0 was accepted as a boolean value!")
except ValueError:
    print("2.0 correctly rejected")

print("\nThe issue: The boolean validator uses 'x in [False, 0, ...]' which")
print("allows floats like 0.0 to pass because 0.0 == 0 in Python.")
print("This violates the expected behavior of only accepting specific boolean-like values.")