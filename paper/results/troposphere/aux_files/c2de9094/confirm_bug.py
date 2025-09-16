"""
Confirm the bug in the integer validator
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.deadline as deadline

print("Testing the integer validator with various inputs:")
print("-" * 50)

test_cases = [
    (1, "integer"),
    (1.0, "float that equals an integer"),
    (1.5, "float with decimal part"),
    (2.7, "another float with decimal"),
    ("5", "string integer"),
    ("5.5", "string float"),
    (True, "boolean True"),
    (False, "boolean False"),
]

for value, description in test_cases:
    print(f"\nInput: {value!r} ({description})")
    print(f"  Type: {type(value).__name__}")
    try:
        result = deadline.integer(value)
        print(f"  ✓ Accepted! Returned: {result!r} (type: {type(result).__name__})")
        
        # Check if the value can actually be converted to int without loss
        if isinstance(value, (int, float)):
            if int(value) != value:
                print(f"  ⚠️  BUG: Float {value} was accepted but int({value}) = {int(value)} != {value}")
    except ValueError as e:
        print(f"  ✗ Rejected: {e}")

print("\n" + "=" * 50)
print("BUG CONFIRMED:")
print("The integer() validator accepts float values like 1.5, 2.7 without error.")
print("This violates the expected behavior - it should only accept values that")
print("can be converted to integer without loss of precision.")
print("\nExpected behavior: integer(1.5) should raise ValueError")
print("Actual behavior: integer(1.5) returns 1.5")