#!/usr/bin/env python3
"""Direct testing of troposphere.backup validators"""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test the backup_vault_name function directly
vault_name_re = re.compile(r"^[a-zA-Z0-9\-\_\.]{1,50}$")

# Check some edge cases
test_cases = [
    ("", False),  # Empty string
    ("-", True),   # Single hyphen
    ("_", True),   # Single underscore  
    (".", True),   # Single period
    ("a-b_c.d", True),  # Mix of valid chars
    ("test@vault", False),  # Invalid char @
    ("test vault", False),  # Space
    ("a" * 50, True),   # Exactly 50 chars
    ("a" * 51, False),  # 51 chars
    ("123", True),      # All numbers
    ("..", True),       # Two periods
    ("...", True),      # Three periods
    ("-.-", True),      # Mix
    ("_._", True),      # Mix
    ("test\nvault", False),  # Newline
    ("test\tvault", False),  # Tab
]

print("Testing regex pattern directly:")
for test_str, expected in test_cases:
    matches = bool(vault_name_re.match(test_str))
    status = "✓" if matches == expected else "ERROR"
    print(f"  {status} '{test_str}' -> {matches} (expected {expected})")

# Now test the actual function
from troposphere.validators.backup import backup_vault_name

print("\nTesting backup_vault_name function:")
for test_str, should_pass in test_cases:
    try:
        result = backup_vault_name(test_str)
        if should_pass:
            print(f"  ✓ '{test_str}' accepted -> '{result}'")
        else:
            print(f"  ERROR: '{test_str}' should have been rejected but got '{result}'")
    except ValueError as e:
        if not should_pass:
            print(f"  ✓ '{test_str}' rejected")
        else:
            print(f"  ERROR: '{test_str}' should have been accepted but was rejected")

# Now let's test the boolean validator more thoroughly
from troposphere.validators import boolean

print("\nTesting boolean validator:")
boolean_test_cases = [
    (True, True, True),
    (False, False, True),
    (1, True, True),
    (0, False, True),
    ("1", True, True),
    ("0", False, True),
    ("true", True, True),
    ("false", False, True),
    ("True", True, True),
    ("False", False, True),
    (2, None, False),  # Should raise
    (-1, None, False),  # Should raise
    ("yes", None, False),  # Should raise
    ("no", None, False),  # Should raise
    ("", None, False),  # Should raise
    (None, None, False),  # Should raise
]

for input_val, expected_output, should_succeed in boolean_test_cases:
    try:
        result = boolean(input_val)
        if should_succeed:
            if result == expected_output:
                print(f"  ✓ {repr(input_val)} -> {result}")
            else:
                print(f"  ERROR: {repr(input_val)} -> {result} (expected {expected_output})")
        else:
            print(f"  ERROR: {repr(input_val)} should have raised but got {result}")
    except (ValueError, TypeError) as e:
        if not should_succeed:
            print(f"  ✓ {repr(input_val)} raised exception")
        else:
            print(f"  ERROR: {repr(input_val)} raised when it shouldn't")

# Test json_checker
from troposphere.validators import json_checker
import json

print("\nTesting json_checker:")

# Test with nested dict
nested_dict = {
    "level1": {
        "level2": {
            "level3": "value"
        }
    }
}

try:
    result = json_checker(nested_dict)
    parsed = json.loads(result)
    if parsed == nested_dict:
        print(f"  ✓ Nested dict round-trips correctly")
    else:
        print(f"  ERROR: Nested dict doesn't match after round-trip")
except Exception as e:
    print(f"  ERROR: Nested dict failed: {e}")

# Test with empty dict
try:
    result = json_checker({})
    parsed = json.loads(result)
    if parsed == {}:
        print(f"  ✓ Empty dict round-trips correctly")
    else:
        print(f"  ERROR: Empty dict doesn't match")
except Exception as e:
    print(f"  ERROR: Empty dict failed: {e}")

# Test idempotence
test_dict = {"test": "value"}
try:
    json_str1 = json_checker(test_dict)
    json_str2 = json_checker(json_str1)
    if json_str1 == json_str2:
        print(f"  ✓ json_checker is idempotent for JSON strings")
    else:
        print(f"  ERROR: Not idempotent: '{json_str1}' != '{json_str2}'")
except Exception as e:
    print(f"  ERROR: Idempotence test failed: {e}")

print("\nDirect testing completed.")