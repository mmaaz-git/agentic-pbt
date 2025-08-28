#!/usr/bin/env python3
"""Test the boolean validator for edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# The boolean function code:
# def boolean(x: Any) -> bool:
#     if x in [True, 1, "1", "true", "True"]:
#         return True
#     if x in [False, 0, "0", "false", "False"]:
#         return False
#     raise ValueError

print("Testing boolean validator:")
print("=" * 50)

# Test cases that should work
test_cases = [
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    ("1", True),
    ("0", False),
    ("true", True),
    ("false", False),
    ("True", True),
    ("False", False),
]

print("\nExpected behavior:")
for input_val, expected in test_cases:
    try:
        result = boolean(input_val)
        if result == expected:
            print(f"  ✓ boolean({repr(input_val)}) = {result}")
        else:
            print(f"  ✗ boolean({repr(input_val)}) = {result}, expected {expected}")
    except Exception as e:
        print(f"  ✗ boolean({repr(input_val)}) raised {e}")

# Test edge cases that should raise ValueError
print("\nEdge cases (should raise ValueError):")
edge_cases = [
    2,
    -1,
    "yes",
    "no",
    "TRUE",  # All caps
    "FALSE", # All caps
    "tRue",  # Mixed case
    "fAlse", # Mixed case
    "",
    None,
    [],
    {},
]

for val in edge_cases:
    try:
        result = boolean(val)
        print(f"  ✗ boolean({repr(val)}) = {result} (should have raised ValueError)")
    except ValueError:
        print(f"  ✓ boolean({repr(val)}) raised ValueError")
    except Exception as e:
        print(f"  ? boolean({repr(val)}) raised {type(e).__name__}: {e}")

# The code looks correct for the boolean validator.
# Let me check if there's an issue with the type hints vs actual behavior

print("\n" + "=" * 50)
print("Type checking:")
result_true = boolean(True)
result_1 = boolean(1)
print(f"boolean(True) is True: {result_true is True}")
print(f"boolean(1) is True: {result_1 is True}")
print(f"type(boolean(True)): {type(result_true)}")
print(f"type(boolean(1)): {type(result_1)}")