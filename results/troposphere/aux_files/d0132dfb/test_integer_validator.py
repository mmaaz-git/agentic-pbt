#!/usr/bin/env python3
"""
Test the integer validator to see if it has better error messages.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Test valid values
print("Testing valid integer values:")
print(f"integer(42) = {integer(42)}")
print(f"integer('42') = {integer('42')}")

# Test invalid value
print("\nTesting invalid integer value:")
try:
    result = integer("not_a_number")
    print(f"integer('not_a_number') = {result}")
except ValueError as e:
    print(f"ValueError raised with message: '{e}'")
    print("Good: The integer validator provides a helpful error message!")