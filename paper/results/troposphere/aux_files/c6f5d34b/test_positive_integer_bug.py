#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import positive_integer

print("Testing positive_integer validator for float handling:")
print("="*50)

test_values = [
    (0, 0, "Integer 0 should return 0"),
    (0.0, "ERROR?", "Float 0.0 - should it be accepted?"),
    (1, 1, "Integer 1 should return 1"),
    (1.0, "ERROR?", "Float 1.0 - should it be accepted?"),
    (1.5, "ERROR", "Float 1.5 should raise error"),
    ("0", "0", "String '0' should return '0'"),
    ("1", "1", "String '1' should return '1'"),
    (-1, "ERROR", "Negative integer should raise error"),
    (-1.0, "ERROR?", "Negative float should raise error"),
]

for value, expected, description in test_values:
    print(f"\nTesting: {description}")
    print(f"  Input: {value!r} (type: {type(value).__name__})")
    try:
        result = positive_integer(value)
        if "ERROR" in str(expected):
            print(f"  ⚠️  Accepted value: returned {result!r}")
            # Try to convert to int to see if it would fail
            try:
                int_val = int(result)
                print(f"  Converts to int: {int_val}")
            except:
                print(f"  Cannot convert to int")
        else:
            print(f"  ✓ Returned: {result!r}")
    except (ValueError, TypeError) as e:
        if "ERROR" in str(expected):
            print(f"  ✓ Correctly raised error: {e}")
        else:
            print(f"  ❌ Unexpected error: {e}")

print("\n" + "="*50)

# Let's look at the actual implementation
print("\nChecking implementation logic:")
print("The positive_integer function calls integer() first")
print("Let's test integer() directly:")

from troposphere.validators import integer

test_floats = [0.0, 1.0, 1.5, -1.0]
for val in test_floats:
    print(f"\ninteger({val!r}):")
    try:
        result = integer(val)
        print(f"  Returned: {result!r}")
        print(f"  int({result!r}) = {int(result)}")
    except (ValueError, TypeError) as e:
        print(f"  Raised: {e}")