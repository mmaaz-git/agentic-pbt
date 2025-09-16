#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer, double

# Test 1: Boolean validator
print("Testing boolean validator...")
test_cases = [
    (True, True),
    (1, True), 
    ("1", True),
    ("true", True),
    ("True", True),
    (False, False),
    (0, False),
    ("0", False),
    ("false", False),
    ("False", False),
]

for input_val, expected in test_cases:
    result = boolean(input_val)
    assert result == expected, f"boolean({input_val}) = {result}, expected {expected}"
    print(f"  boolean({input_val!r}) = {result}")

# Test some invalid inputs
invalid_inputs = ["yes", "no", 2, -1, None, [], {}, ""]
for invalid in invalid_inputs:
    try:
        result = boolean(invalid)
        print(f"  ERROR: boolean({invalid!r}) should raise ValueError but returned {result}")
    except ValueError:
        print(f"  boolean({invalid!r}) correctly raised ValueError")

# Test 2: Integer validator
print("\nTesting integer validator...")
valid_integers = [0, 1, -1, 100, "42", "-100", "0"]
for val in valid_integers:
    result = integer(val)
    assert result == val
    print(f"  integer({val!r}) = {result}")

# Test invalid integers
invalid_integers = ["abc", "", None, [], 1.5]
for invalid in invalid_integers:
    try:
        result = integer(invalid)
        print(f"  ERROR: integer({invalid!r}) should raise ValueError but returned {result}")
    except ValueError:
        print(f"  integer({invalid!r}) correctly raised ValueError")

# Test 3: Double validator
print("\nTesting double validator...")
valid_doubles = [0, 1.5, -2.7, "3.14", "-9.8", 100, "100"]
for val in valid_doubles:
    result = double(val)
    assert result == val
    print(f"  double({val!r}) = {result}")

# Test invalid doubles
invalid_doubles = ["abc", "", None, []]
for invalid in invalid_doubles:
    try:
        result = double(invalid)
        print(f"  ERROR: double({invalid!r}) should raise ValueError but returned {result}")
    except ValueError:
        print(f"  double({invalid!r}) correctly raised ValueError")

print("\nAll basic tests passed!")