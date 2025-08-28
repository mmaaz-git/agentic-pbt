#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

print("Testing boolean validator consistency...")

# Test case sensitivity issue
test_cases = [
    # Input, Expected Result, Description
    ("true", True, "lowercase true"),
    ("True", True, "titlecase True"),
    ("TRUE", None, "uppercase TRUE - should fail"),
    ("false", False, "lowercase false"),
    ("False", False, "titlecase False"),
    ("FALSE", None, "uppercase FALSE - should fail"),
    ("tRuE", None, "mixed case tRuE - should fail"),
    ("1", True, "string 1"),
    ("0", False, "string 0"),
]

failures = []
for input_val, expected, description in test_cases:
    try:
        result = boolean(input_val)
        if expected is None:
            failures.append(f"UNEXPECTED SUCCESS: {description} ({input_val}) returned {result}, expected ValueError")
        elif result != expected:
            failures.append(f"WRONG VALUE: {description} ({input_val}) returned {result}, expected {expected}")
        else:
            print(f"✓ {description}: {input_val} -> {result}")
    except ValueError as e:
        if expected is not None:
            failures.append(f"UNEXPECTED FAILURE: {description} ({input_val}) raised ValueError, expected {expected}")
        else:
            print(f"✓ {description}: {input_val} -> ValueError (as expected)")

if failures:
    print("\nINCONSISTENCIES FOUND:")
    for f in failures:
        print(f"  - {f}")
else:
    print("\nAll tests passed as expected!")

# Additional test: Check if "1" and 1 produce same result
print("\n\nTesting string vs integer consistency:")
str_result = boolean("1")
int_result = boolean(1)
print(f'boolean("1") = {str_result}')
print(f'boolean(1) = {int_result}')
print(f"Consistent: {str_result == int_result}")

# Test the specific line from the code
print("\n\nExact values accepted by boolean validator:")
print(f"True values: {[True, 1, '1', 'true', 'True']}")
print(f"False values: {[False, 0, '0', 'false', 'False']}")

# Property test: Does boolean handle byte strings?
print("\n\nTesting byte strings:")
try:
    result = boolean(b"true")
    print(f"boolean(b'true') = {result} - UNEXPECTED SUCCESS")
except (ValueError, TypeError) as e:
    print(f"boolean(b'true') raised {type(e).__name__} - as expected")