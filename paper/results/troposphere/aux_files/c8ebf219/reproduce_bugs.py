"""Minimal reproductions of bugs found in troposphere.dynamodb"""

import troposphere.dynamodb as ddb

print("Bug 1: integer() accepts non-integer floats")
print("=" * 50)

# integer() should reject non-integer floats but doesn't
test_floats = [0.5, 1.5, 2.7, -3.14, 999.999]
for f in test_floats:
    try:
        result = ddb.integer(f)
        print(f"  ddb.integer({f}) = {result} (BUG: should raise ValueError)")
    except ValueError as e:
        print(f"  ddb.integer({f}) correctly raised ValueError: {e}")

print("\nBug 2: Type conversion functions don't convert strings")
print("=" * 50)

# integer() should convert string to int but returns string
int_strings = ['0', '42', '-100', '999']
for s in int_strings:
    result = ddb.integer(s)
    print(f"  ddb.integer('{s}') = {repr(result)} (type: {type(result).__name__})")
    print(f"    Expected: {int(s)} (type: int)")

print()

# double() should convert string to float but returns string  
float_strings = ['0.0', '3.14', '-2.5', '1e6']
for s in float_strings:
    result = ddb.double(s)
    print(f"  ddb.double('{s}') = {repr(result)} (type: {type(result).__name__})")
    print(f"    Expected: {float(s)} (type: float)")

print("\nImpact Analysis:")
print("=" * 50)
print("These bugs could cause issues in CloudFormation template generation:")
print("1. Non-integer values passed to integer fields won't be caught")
print("2. String values won't be converted to proper numeric types")
print("3. This could lead to invalid CloudFormation templates or unexpected behavior")