#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test that 0.0 (float) is incorrectly accepted
print("Testing boolean validator with float 0.0:")
try:
    result = boolean(0.0)
    print(f"boolean(0.0) = {result} (type: {type(result)})")
    print("BUG: Float 0.0 should not be accepted, but it returns False")
except ValueError as e:
    print(f"Correctly rejected: {e}")

# Test that 1.0 is also incorrectly accepted
print("\nTesting boolean validator with float 1.0:")
try:
    result = boolean(1.0)
    print(f"boolean(1.0) = {result} (type: {type(result)})")
    print("BUG: Float 1.0 should not be accepted, but it returns True")
except ValueError as e:
    print(f"Correctly rejected: {e}")

# Test other float values
print("\nTesting boolean validator with float 0.5:")
try:
    result = boolean(0.5)
    print(f"boolean(0.5) = {result}")
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\nExpected behavior per the code:")
print("- Should accept: True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'")
print("- Should reject: floats, other strings, other types")