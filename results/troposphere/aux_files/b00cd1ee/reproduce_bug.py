#!/usr/bin/env python3
"""Minimal reproduction of environment variable validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.awslambda import Function, Environment, Code

# Try to create a Lambda function with invalid environment variable names
# According to AWS documentation, environment variable names must:
# - Start with a letter
# - Contain only letters, numbers, and underscores

print("Testing Lambda Function environment variable validation...")
print()

# This should fail but doesn't - contains invalid characters
invalid_names = {
    "MY_VAR:PROD": "value1",    # Contains colon
    "API-KEY": "value2",         # Contains hyphen
    "DB.HOST": "value3",         # Contains dot
    "USER@NAME": "value4",       # Contains @
    "PATH/TO/FILE": "value5"     # Contains slash
}

print("Attempting to create Function with invalid variable names:")
for name in invalid_names:
    print(f"  {name}: contains invalid character '{[c for c in name if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'][0] if [c for c in name if c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'] else ''}'")

try:
    func = Function(
        "TestFunction",
        Code=Code(ImageUri="test-image"),
        Role="arn:aws:iam::123456789012:role/lambda-role",
        Environment=Environment(Variables=invalid_names)
    )
    print("\n❌ BUG CONFIRMED: Function created with invalid environment variable names!")
    print("This would fail when deployed to AWS with an error like:")
    print("  'Environment variable name contains invalid characters'")
    
except ValueError as e:
    print(f"\n✓ Validation correctly rejected invalid names: {e}")

print("\n" + "="*60)
print("Directly testing the validation function:")

from troposphere.validators.awslambda import validate_variables_name

# Test individual problematic names
test_cases = [
    ("VALID_NAME", True),
    ("MY_VAR123", True),
    ("MY:VAR", False),  # Colon should be invalid
    ("MY-VAR", False),  # Hyphen should be invalid
    ("MY.VAR", False),  # Dot should be invalid
    ("MY VAR", False),  # Space should be invalid
    ("123VAR", False),  # Starting with number should be invalid
    ("_VAR", False),    # Starting with underscore should be invalid
]

for name, should_pass in test_cases:
    try:
        result = validate_variables_name({name: "value"})
        if should_pass:
            print(f"✓ '{name}': Correctly accepted")
        else:
            print(f"❌ '{name}': BUG - Should have been rejected but was accepted!")
    except ValueError:
        if not should_pass:
            print(f"✓ '{name}': Correctly rejected")
        else:
            print(f"❌ '{name}': Should have been accepted but was rejected!")