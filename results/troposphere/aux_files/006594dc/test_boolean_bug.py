#!/usr/bin/env python3
"""Test for potential bug in boolean validator"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# According to the code at line 39-40 in validators/__init__.py:
# if x in [True, 1, "1", "true", "True"]:
#     return True

# This means it checks with == comparison, not identity
# Let's test if there's any issue with the string "1" vs integer 1

print("Testing boolean validator implementation...")

# These should all return True
test_true_values = [True, 1, "1", "true", "True"]
for val in test_true_values:
    try:
        result = boolean(val)
        if result is not True:  # Check identity, not just equality
            print(f"POTENTIAL BUG: boolean({repr(val)}) returned {repr(result)} (type: {type(result)})")
            print(f"  Result is True: {result is True}")
            print(f"  Result == True: {result == True}")
        else:
            print(f"OK: boolean({repr(val)}) = True")
    except Exception as e:
        print(f"ERROR: boolean({repr(val)}) raised {e}")

# These should all return False
test_false_values = [False, 0, "0", "false", "False"]
for val in test_false_values:
    try:
        result = boolean(val)
        if result is not False:  # Check identity, not just equality
            print(f"POTENTIAL BUG: boolean({repr(val)}) returned {repr(result)} (type: {type(result)})")
            print(f"  Result is False: {result is False}")
            print(f"  Result == False: {result == False}")
        else:
            print(f"OK: boolean({repr(val)}) = False")
    except Exception as e:
        print(f"ERROR: boolean({repr(val)}) raised {e}")

# Test edge case: What if someone passes the string "True" with extra whitespace?
edge_cases = [" true", "true ", " True ", "TRUE", "FALSE", "Yes", "No", "1.0", "0.0"]
print("\nTesting edge cases that should raise ValueError:")
for val in edge_cases:
    try:
        result = boolean(val)
        print(f"ISSUE: boolean({repr(val)}) = {repr(result)} (should have raised ValueError)")
    except ValueError:
        print(f"OK: boolean({repr(val)}) correctly raised ValueError")