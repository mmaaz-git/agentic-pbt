#!/usr/bin/env python3
"""
Minimal reproduction of boolean validator bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test case that should fail but doesn't
test_value = 0.0

print(f"Testing boolean({test_value})")
try:
    result = boolean(test_value)
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    
    # According to the code, boolean should only accept:
    # True, 1, "1", "true", "True" -> True
    # False, 0, "0", "false", "False" -> False
    # Everything else should raise ValueError
    
    print("\nThe boolean() function incorrectly accepts float 0.0 and returns False")
    print("Expected: ValueError")
    print(f"Actual: Returns {result}")
    
    # Let's test a few more edge cases
    print("\n--- Testing more edge cases ---")
    test_cases = [0.0, 1.0, 0.5, -1, 2, "1.0", "0.0"]
    for test in test_cases:
        try:
            res = boolean(test)
            print(f"boolean({test!r}) = {res} (should raise ValueError)")
        except ValueError:
            print(f"boolean({test!r}) correctly raises ValueError")
            
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")