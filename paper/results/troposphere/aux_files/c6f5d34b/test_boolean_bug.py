#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Reproduce the boolean validator bug
print("Testing boolean validator bug:")
print("="*50)

# The validator accepts 0.0 (float) when it should only accept specific values
test_values = [
    (0, False, "Integer 0 should return False"),
    (0.0, "ERROR", "Float 0.0 should raise ValueError"),
    (1, True, "Integer 1 should return True"),
    (1.0, "ERROR", "Float 1.0 should raise ValueError"),
    (False, False, "Boolean False should return False"),
    (True, True, "Boolean True should return True"),
    ("0", False, "String '0' should return False"),
    ("1", True, "String '1' should return True"),
    (2, "ERROR", "Integer 2 should raise ValueError"),
    (2.0, "ERROR", "Float 2.0 should raise ValueError"),
]

for value, expected, description in test_values:
    print(f"\nTesting: {description}")
    print(f"  Input: {value!r} (type: {type(value).__name__})")
    try:
        result = boolean(value)
        if expected == "ERROR":
            print(f"  ❌ BUG: Expected ValueError but got {result}")
        else:
            if result == expected:
                print(f"  ✓ Correct: returned {result}")
            else:
                print(f"  ❌ BUG: Expected {expected} but got {result}")
    except ValueError as e:
        if expected == "ERROR":
            print(f"  ✓ Correct: raised ValueError as expected")
        else:
            print(f"  ❌ BUG: Unexpected ValueError, expected {expected}")

print("\n" + "="*50)
print("SUMMARY: The boolean validator incorrectly accepts float values 0.0 and 1.0")
print("This happens because Python treats 0.0 == 0 and 1.0 == 1 as True")
print("The validator should use isinstance() or type checking to reject floats")