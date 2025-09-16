#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.pkg.utils import validate_multiselect

# Bug: validate_multiselect fails with nested lists
nested_list = [["item1"]]
json_str = json.dumps(nested_list)

print(f"Input: {nested_list}")
print(f"JSON string: {json_str}")

try:
    result = validate_multiselect(json_str)
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    print("\nExpected: The function should handle nested lists correctly")
    print("Actual: It throws a ValidationError expecting str type")