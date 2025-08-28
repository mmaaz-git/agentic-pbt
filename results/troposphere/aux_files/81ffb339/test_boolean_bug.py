#!/usr/bin/env python3
"""Test for potential bug in boolean validator."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test the documented behavior vs actual behavior
# According to the code, it should accept "1" and 1
print("Testing boolean validator:")

# These should work according to code
test_values = [
    (True, True),
    (1, True),
    ("1", True),
    ("true", True),
    ("True", True),
    (False, False),
    (0, False),
    ("0", False),
    ("false", False),
    ("False", False),
]

for value, expected in test_values:
    try:
        result = boolean(value)
        print(f"boolean({repr(value)}) = {result}, expected {expected}, match={result == expected}")
    except Exception as e:
        print(f"boolean({repr(value)}) raised {e}")

# Now let's check the actual code behavior more carefully
print("\n\nChecking code logic:")
print("Line 39 checks: x in [True, 1, '1', 'true', 'True']")
print("But actual string '1' != integer 1")

# Edge case testing
print("\n\nEdge cases:")
edge_cases = ["TRUE", "FALSE", "True ", " True", "1.0", 1.0, "yes", "no", "", None]
for value in edge_cases:
    try:
        result = boolean(value)
        print(f"boolean({repr(value)}) = {result}")
    except ValueError:
        print(f"boolean({repr(value)}) raised ValueError")
    except Exception as e:
        print(f"boolean({repr(value)}) raised {type(e).__name__}: {e}")