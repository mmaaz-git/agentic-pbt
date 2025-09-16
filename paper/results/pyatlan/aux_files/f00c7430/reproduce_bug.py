#!/usr/bin/env python3
"""Minimal reproduction of the bug in VCRPrettyPrintJSONBody.deserialize"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.test_utils.base_vcr import VCRPrettyPrintJSONBody

# Test case that causes the bug
test_input = '0'

print(f"Testing with input: {test_input}")
print(f"Input type: {type(test_input)}")

try:
    result = VCRPrettyPrintJSONBody.deserialize(test_input)
    print(f"Result: {result}")
except AttributeError as e:
    print(f"Bug confirmed! AttributeError: {e}")
    print(f"The issue is that json.loads('0') returns 0 (int), not a dict")
    
# Other problematic inputs
problematic_inputs = [
    '0',
    '42',
    'true',
    'false',
    'null',
    '"string"',
    '[1, 2, 3]',
]

print("\nTesting other problematic inputs:")
for input_str in problematic_inputs:
    try:
        result = VCRPrettyPrintJSONBody.deserialize(input_str)
        print(f"  '{input_str}' -> OK (returned {type(result).__name__})")
    except AttributeError as e:
        print(f"  '{input_str}' -> FAILED with AttributeError")