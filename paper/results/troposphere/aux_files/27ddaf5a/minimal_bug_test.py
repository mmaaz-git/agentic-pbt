#!/usr/bin/env python3
"""Minimal test to find bugs in troposphere.omics."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.omics as omics
from troposphere.validators import boolean

# Test 1: Check boolean validator edge case
print("Test 1: Boolean validator with string '1'")
try:
    result = boolean("1")
    print(f"boolean('1') = {result}")
    print(f"Result type: {type(result)}")
    print(f"Result is True: {result is True}")
    
    # According to the code, "1" should return True
    if result is not True:
        print("BUG FOUND: boolean('1') does not return True")
except Exception as e:
    print(f"Error: {e}")

print("\nTest 2: Boolean validator with integer 1")
try:
    result = boolean(1)
    print(f"boolean(1) = {result}")
    print(f"Result type: {type(result)}")
    print(f"Result is True: {result is True}")
    
    if result is not True:
        print("BUG FOUND: boolean(1) does not return True")
except Exception as e:
    print(f"Error: {e}")

print("\nTest 3: Check if '1' is in the check list")
print(f"'1' in [True, 1, '1', 'true', 'True']: {'1' in [True, 1, '1', 'true', 'True']}")

print("\nTest 4: RunGroup with boolean-typed field (if any)")
# Let's check if WorkflowParameter.Optional uses boolean validator
param = omics.WorkflowParameter()
print(f"WorkflowParameter props: {param.props}")

print("\nTest 5: Setting Optional with string '1'")
try:
    param.Optional = "1"
    dict_repr = param.to_dict()
    print(f"After setting Optional='1': {dict_repr}")
    if "Optional" in dict_repr:
        print(f"Optional value: {dict_repr['Optional']}, type: {type(dict_repr['Optional'])}")
except Exception as e:
    print(f"Error setting Optional: {e}")
    import traceback
    traceback.print_exc()

print("\nTest 6: Checking validator function directly from module")
from troposphere.validators import boolean as bool_validator
print(f"Validator function: {bool_validator}")
print(f"Source location: {bool_validator.__module__}")

# Let's check the actual implementation
import inspect
print("\nBoolean validator source:")
try:
    source = inspect.getsource(bool_validator)
    print(source)
except:
    print("Could not get source")

print("\nTest 7: Testing edge case with actual check")
test_val = "1"
print(f"Testing with value: {test_val!r}")
print(f"Checking condition: {test_val} in [True, 1, '1', 'true', 'True']")
print(f"Result: {test_val in [True, 1, '1', 'true', 'True']}")

# Direct implementation test
def boolean_test(x):
    if x in [True, 1, "1", "true", "True"]:
        return True
    if x in [False, 0, "0", "false", "False"]:
        return False
    raise ValueError

print(f"\nDirect implementation test:")
print(f"boolean_test('1') = {boolean_test('1')}")
print(f"boolean_test('1') is True: {boolean_test('1') is True}")