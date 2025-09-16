"""Minimal reproduction of boolean validator case sensitivity bug."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# The boolean validator has inconsistent case handling
# It accepts "true"/"True" but rejects "TRUE"

print("Testing boolean validator case sensitivity:")
print("-" * 50)

test_values = ["true", "True", "TRUE", "false", "False", "FALSE"]

for value in test_values:
    try:
        result = boolean(value)
        print(f"✓ boolean('{value}') = {result}")
    except ValueError:
        print(f"✗ boolean('{value}') raised ValueError")

print("-" * 50)
print("\nBUG: The validator accepts 'True' but rejects 'TRUE'")
print("This is inconsistent - if it accepts Title case, it should accept UPPER case")