#!/usr/bin/env python3
"""Simple test runner for troposphere.backup"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.backup import backup_vault_name
from troposphere.validators import boolean, integer, double, json_checker

# Test 1: backup_vault_name with edge cases
print("Testing backup_vault_name...")

# Test empty string
try:
    result = backup_vault_name("")
    print(f"  ERROR: Empty string accepted: '{result}'")
except ValueError as e:
    print(f"  ✓ Empty string rejected: {e}")

# Test string with only a hyphen
try:
    result = backup_vault_name("-")
    print(f"  ✓ Single hyphen accepted: '{result}'")
except ValueError as e:
    print(f"  ERROR: Single hyphen rejected: {e}")

# Test string with only a period
try:
    result = backup_vault_name(".")
    print(f"  ✓ Single period accepted: '{result}'")
except ValueError as e:
    print(f"  ERROR: Single period rejected: {e}")

# Test string with only underscore
try:
    result = backup_vault_name("_")
    print(f"  ✓ Single underscore accepted: '{result}'")
except ValueError as e:
    print(f"  ERROR: Single underscore rejected: {e}")

# Test exactly 50 characters
name_50 = "a" * 50
try:
    result = backup_vault_name(name_50)
    print(f"  ✓ 50 character name accepted")
except ValueError as e:
    print(f"  ERROR: 50 character name rejected: {e}")

# Test 51 characters
name_51 = "a" * 51
try:
    result = backup_vault_name(name_51)
    print(f"  ERROR: 51 character name accepted")
except ValueError as e:
    print(f"  ✓ 51 character name rejected")

# Test with special characters in the allowed set
test_names = [
    "valid-name",
    "valid_name",
    "valid.name",
    "valid-name_with.all",
    "123",
    "a1b2c3",
]

for name in test_names:
    try:
        result = backup_vault_name(name)
        print(f"  ✓ '{name}' accepted")
    except ValueError as e:
        print(f"  ERROR: '{name}' rejected: {e}")

# Test boolean validator edge cases
print("\nTesting boolean validator...")

# Test with string "1" 
try:
    result = boolean("1")
    if result is True:
        print(f"  ✓ '1' converts to True")
    else:
        print(f"  ERROR: '1' converts to {result}")
except Exception as e:
    print(f"  ERROR: '1' raises: {e}")

# Test with int 1
try:
    result = boolean(1)
    if result is True:
        print(f"  ✓ 1 converts to True")
    else:
        print(f"  ERROR: 1 converts to {result}")
except Exception as e:
    print(f"  ERROR: 1 raises: {e}")

# Test json_checker
print("\nTesting json_checker...")

# Test with dict
test_dict = {"key": "value", "number": 123}
try:
    result = json_checker(test_dict)
    if isinstance(result, str):
        # Try to parse it back
        import json
        parsed = json.loads(result)
        if parsed == test_dict:
            print(f"  ✓ Dict round-trips correctly")
        else:
            print(f"  ERROR: Dict doesn't round-trip: {parsed} != {test_dict}")
    else:
        print(f"  ERROR: Dict doesn't convert to string: {result}")
except Exception as e:
    print(f"  ERROR: Dict processing failed: {e}")

# Test with valid JSON string
json_str = '{"key": "value"}'
try:
    result = json_checker(json_str)
    if result == json_str:
        print(f"  ✓ Valid JSON string passes through")
    else:
        print(f"  ERROR: JSON string modified: {result}")
except Exception as e:
    print(f"  ERROR: JSON string failed: {e}")

# Test with invalid JSON string
invalid_json = '{"key": value}'  # Missing quotes around value
try:
    result = json_checker(invalid_json)
    print(f"  ERROR: Invalid JSON accepted: {result}")
except Exception as e:
    print(f"  ✓ Invalid JSON rejected: {e}")

print("\nAll manual tests completed.")