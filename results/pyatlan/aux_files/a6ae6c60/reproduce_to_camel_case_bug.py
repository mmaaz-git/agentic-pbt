#!/usr/bin/env python3
"""
Minimal reproduction of the to_camel_case idempotence bug.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages/')

from pyatlan.utils import to_camel_case

# Test case found by Hypothesis
test_input = 'A_A'

# Apply to_camel_case once
once = to_camel_case(test_input)
print(f"Input: '{test_input}'")
print(f"First application: '{once}'")

# Apply to_camel_case twice
twice = to_camel_case(once)
print(f"Second application: '{twice}'")

# Check idempotence
if once != twice:
    print(f"\n❌ BUG CONFIRMED: Function is not idempotent!")
    print(f"   '{test_input}' -> '{once}' -> '{twice}'")
    
    # Test more examples to understand the pattern
    print("\nAdditional test cases:")
    test_cases = ['B_B', 'Test_Case', 'UPPER_CASE', 'lower_case', 'Mixed_CaSe_Test']
    
    for test in test_cases:
        result1 = to_camel_case(test)
        result2 = to_camel_case(result1)
        if result1 != result2:
            print(f"   '{test}' -> '{result1}' -> '{result2}' ❌")
        else:
            print(f"   '{test}' -> '{result1}' -> '{result2}' ✓")
else:
    print("\n✓ No bug found")