#!/usr/bin/env python3
"""Confirm boolean validator bug with float values."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

print("BOOLEAN VALIDATOR BUG INVESTIGATION")
print("="*50)

print("\nBackground: Python's equality semantics")
print(f"1 == True: {1 == True}")
print(f"0 == False: {0 == False}") 
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 == True: {1.0 == True}")
print(f"0.0 == False: {0.0 == False}")

print("\nThe boolean validator implementation:")
print("def boolean(x):")
print('    if x in [True, 1, "1", "true", "True"]:')
print("        return True")
print('    if x in [False, 0, "0", "false", "False"]:')
print("        return False")
print("    raise ValueError")

print("\n" + "="*50)
print("BUG DEMONSTRATION:")

# The bug: floats 1.0 and 0.0 are accepted due to Python's equality
test_cases = [
    (1.0, "Should raise ValueError but returns True"),
    (0.0, "Should raise ValueError but returns False"),
    (2.0, "Should raise ValueError"),
    (-1.0, "Should raise ValueError"),
    (0.5, "Should raise ValueError"),
    (1.00000001, "Should raise ValueError"),
    (0.99999999, "Should raise ValueError"),
]

bug_confirmed = False

for value, expected_behavior in test_cases:
    try:
        result = boolean(value)
        if "but returns" in expected_behavior:
            print(f"✗ BUG CONFIRMED: boolean({value}) = {result}")
            print(f"  Expected: ValueError")
            print(f"  Actual: Returns {result}")
            bug_confirmed = True
        else:
            print(f"✗ UNEXPECTED: boolean({value}) = {result} (expected ValueError)")
    except ValueError:
        if "but returns" in expected_behavior:
            print(f"✓ OK: boolean({value}) raises ValueError (fixed?)")
        else:
            print(f"✓ OK: boolean({value}) raises ValueError")
    except Exception as e:
        print(f"? UNEXPECTED: boolean({value}) raises {type(e).__name__}: {e}")

print("\n" + "="*50)
print("REPRODUCING THE BUG:")

print("\n# Minimal reproduction code:")
print("from troposphere.validators import boolean")
print("")
print("# These should raise ValueError according to the intended behavior")
print("# but they return boolean values due to Python's equality semantics")
print("")
print("result1 = boolean(1.0)  # Returns True, should raise ValueError")
print("result2 = boolean(0.0)  # Returns False, should raise ValueError")
print("")
print("# The bug occurs because:")
print("# 1.0 == 1 == True in Python")
print("# 0.0 == 0 == False in Python")
print("# So 1.0 matches when checking 'if x in [True, 1, ...]'")

print("\n" + "="*50)
print("IMPACT ANALYSIS:")

print("\n1. Where is boolean validator used?")
print("   - WorkflowParameter.Optional field")
print("   - Any other boolean-typed properties in troposphere")

print("\n2. What's the impact?")
print("   - Users might accidentally pass float values")
print("   - The validator silently accepts them instead of raising an error")
print("   - This could lead to unexpected behavior in CloudFormation templates")

print("\n3. Real-world scenario:")
print("   param = omics.WorkflowParameter()")
print("   param.Optional = 1.0  # Accidentally passed float instead of boolean")
print("   # This should fail but doesn't")

# Test with actual WorkflowParameter
import troposphere.omics as omics

print("\n" + "="*50)
print("TESTING WITH ACTUAL WORKFLOWPARAMETER:")

param = omics.WorkflowParameter()
try:
    param.Optional = 1.0
    param_dict = param.to_dict()
    print(f"✗ BUG: WorkflowParameter.Optional accepted 1.0")
    print(f"  Result: {param_dict}")
    bug_confirmed = True
except (ValueError, TypeError) as e:
    print(f"✓ WorkflowParameter.Optional rejected 1.0: {e}")

try:
    param.Optional = 0.0
    param_dict = param.to_dict()
    print(f"✗ BUG: WorkflowParameter.Optional accepted 0.0")
    print(f"  Result: {param_dict}")
    bug_confirmed = True
except (ValueError, TypeError) as e:
    print(f"✓ WorkflowParameter.Optional rejected 0.0: {e}")

print("\n" + "="*50)
if bug_confirmed:
    print("BUG STATUS: CONFIRMED ✗")
    print("\nThe boolean validator incorrectly accepts float values 1.0 and 0.0")
    print("due to Python's equality semantics (1.0 == 1 == True, 0.0 == 0 == False)")
else:
    print("BUG STATUS: NOT FOUND ✓")
    print("\nThe boolean validator correctly rejects all tested values")