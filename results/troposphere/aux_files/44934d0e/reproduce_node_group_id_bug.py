#!/usr/bin/env python3
"""Minimal reproduction of validate_node_group_id bug"""

from troposphere.validators.elasticache import validate_node_group_id

# Test case that should fail but doesn't
test_input = "0:"
print(f"Testing input: '{test_input}'")

try:
    result = validate_node_group_id(test_input)
    print(f"✗ BUG: Function accepted '{test_input}' and returned '{result}'")
    print(f"  This is invalid because '0:' does not match the pattern ^\\d{{1,4}}$")
except ValueError as e:
    print(f"✓ Correctly rejected: {e}")

# Another example
test_input2 = "123abc"
print(f"\nTesting input: '{test_input2}'")

try:
    result = validate_node_group_id(test_input2)
    print(f"✗ BUG: Function accepted '{test_input2}' and returned '{result}'")
    print(f"  This is invalid because '123abc' contains non-digit characters")
except ValueError as e:
    print(f"✓ Correctly rejected: {e}")

# Valid input for comparison
test_input3 = "1234"
print(f"\nTesting input: '{test_input3}'")

try:
    result = validate_node_group_id(test_input3)
    print(f"✓ Correctly accepted '{test_input3}' and returned '{result}'")
except ValueError as e:
    print(f"✗ Incorrectly rejected: {e}")