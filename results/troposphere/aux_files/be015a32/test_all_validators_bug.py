#!/usr/bin/env python
"""Test all validators with the string formatting bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.glue import (
    connection_type_validator,
    delete_behavior_validator,
    update_behavior_validator,
    table_type_validator,
    trigger_type_validator
)

validators_to_test = [
    (connection_type_validator, "INVALID_CONNECTION", "ConnectionType"),
    (delete_behavior_validator, "INVALID_BEHAVIOR", "DeleteBehavior"),
    (update_behavior_validator, "INVALID_UPDATE", "UpdateBehavior"),
    (table_type_validator, "INVALID_TABLE", "TableType"),
    (trigger_type_validator, "INVALID_TRIGGER", "Type")
]

print("Testing all validators for string formatting bug...")
print("=" * 60)

bugs_found = []

for validator, invalid_input, param_name in validators_to_test:
    print(f"\nTesting {validator.__name__} with input: '{invalid_input}'")
    try:
        result = validator(invalid_input)
        print(f"  ❌ Unexpectedly succeeded with result: {result}")
    except ValueError as e:
        error_msg = str(e)
        print(f"  ValueError: {error_msg}")
        if "%" in error_msg and invalid_input not in error_msg:
            print(f"  ✓ BUG CONFIRMED: Message has '%' instead of '{invalid_input}'")
            bugs_found.append((validator.__name__, param_name))
    except TypeError as e:
        print(f"  TypeError: {e}")
        print(f"  ✓ BUG CONFIRMED: String formatting failed")
        bugs_found.append((validator.__name__, param_name))

print("\n" + "=" * 60)
print(f"Summary: Found {len(bugs_found)} bugs in validators:")
for validator_name, param_name in bugs_found:
    print(f"  - {validator_name} (for {param_name})")