#!/usr/bin/env python3
"""Minimal reproducible test cases for the bugs found."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Parameter

print("=== Bug 1: Parameter accepts empty string as title ===")
print("-" * 50)

# The regex pattern requires at least one alphanumeric character: ^[a-zA-Z0-9]+$
# But empty string is accepted as a valid title
try:
    param = Parameter("", Type="String")
    print(f"BUG CONFIRMED: Created parameter with empty title")
    print(f"  Title: {param.title!r}")
    print(f"  Title length: {len(param.title)}")
    
    # Check if it causes issues when added to template
    from troposphere import Template
    template = Template()
    template.add_parameter(param)
    
    # Try to generate JSON
    json_output = template.to_json()
    print(f"  Template JSON generated successfully")
    print(f"  Parameters in JSON: {list(template.parameters.keys())}")
    
except Exception as e:
    print(f"Empty title rejected: {e}")

print("\n=== Bug 2: Parameter String type accepts non-string defaults ===")
print("-" * 50)

# Test case 1: Integer 0 is accepted
print("\nTest 1: Integer 0 as Default for String type")
try:
    param = Parameter("TestParam1", Type="String", Default=0)
    param.validate()  # Should fail but doesn't
    print(f"BUG CONFIRMED: Integer 0 accepted as Default for String type")
    print(f"  Default value: {param.Default!r}")
    print(f"  Default type: {type(param.Default)}")
except (ValueError, TypeError) as e:
    print(f"Correctly rejected: {e}")

# Test case 2: Boolean False is accepted
print("\nTest 2: Boolean False as Default for String type")
try:
    param = Parameter("TestParam2", Type="String", Default=False)
    param.validate()  # Should fail but doesn't
    print(f"BUG CONFIRMED: Boolean False accepted as Default for String type")
    print(f"  Default value: {param.Default!r}")
    print(f"  Default type: {type(param.Default)}")
except (ValueError, TypeError) as e:
    print(f"Correctly rejected: {e}")

# Test case 3: Other falsy values
print("\nTest 3: Testing why certain values pass validation")
print("Investigating the validation logic...")

# Let's check the actual validation code
import inspect
print(f"\nParameter.validate source:")
lines = inspect.getsource(Parameter.validate).split('\n')
for i, line in enumerate(lines[65:80], 65):  # Show relevant part
    if 'String' in line or 'default' in line:
        print(f"  {i}: {line}")

print("\n=== Impact Analysis ===")
print("-" * 50)
print("Bug 1 (Empty Title):")
print("  - Severity: Low")
print("  - CloudFormation would likely reject the template")
print("  - But library should enforce its own validation rules")

print("\nBug 2 (Type Validation):")
print("  - Severity: Medium")
print("  - Could lead to runtime errors in CloudFormation")  
print("  - Violates the documented type contract")
print("  - Only affects specific 'falsy' values (0, False)")

print("\n=== Root Cause Analysis ===")
print("-" * 50)
print("The validation likely uses a simple truthiness check")
print("that treats 0 and False as 'no default' rather than")
print("checking if default is None specifically.")