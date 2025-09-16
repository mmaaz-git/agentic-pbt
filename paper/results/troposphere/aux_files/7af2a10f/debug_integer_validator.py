"""Debug the integer validator issue."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Test various float values
test_values = [0.0, 1.0, -1.0, 3.14, -3.14, 1e10, float('inf')]

print("Testing integer validator with various float values:")
print("-" * 50)

for val in test_values:
    try:
        result = integer(val)
        print(f"integer({val:10}) -> {result!r:15} (type: {type(result).__name__})")
        try:
            int_val = int(result)
            print(f"  int({result!r}) = {int_val}")
        except:
            print(f"  int({result!r}) raises exception")
    except (ValueError, TypeError) as e:
        print(f"integer({val:10}) -> REJECTED: {e}")

print("\n" + "-" * 50)
print("The issue: integer() accepts float values!")
print("This violates the expected behavior that it should only accept integers.")
print("CloudFormation expects integer types for integer properties.")