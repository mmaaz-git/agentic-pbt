#!/usr/bin/env python3
"""Static analysis to identify potential bugs in troposphere.licensemanager."""

import sys
import ast
import inspect

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import licensemanager, validators, BaseAWSObject

# Analyze the validator functions
print("=== ANALYZING VALIDATOR FUNCTIONS ===\n")

# 1. Boolean validator
print("1. Boolean validator analysis:")
print(f"   Source: {inspect.getsource(validators.boolean)}")
print("   Analysis: The boolean function accepts '1' as string but not '1' as integer?")
print("   - It checks for 1 (int) and '1' (string) separately")
print("   - Potential inconsistency: What about '01' or ' 1 '?")

# 2. Integer validator  
print("\n2. Integer validator analysis:")
print(f"   Source: {inspect.getsource(validators.integer)}")
print("   Analysis: The integer function uses int() to validate but returns the original value")
print("   - Returns x unchanged after validation, not int(x)")
print("   - This means '123' remains a string even after validation")
print("   - Could cause type confusion downstream")

# 3. Check the props definitions in license manager classes
print("\n=== ANALYZING LICENSEMANAGER CLASSES ===\n")

# Check Grant class
print("Grant class props:")
for prop_name, (prop_type, required) in licensemanager.Grant.props.items():
    print(f"  {prop_name}: type={prop_type}, required={required}")

print("\nLicense class props:")
for prop_name, (prop_type, required) in licensemanager.License.props.items():
    print(f"  {prop_name}: type={prop_type}, required={required}")

# 4. Check validation logic in BaseAWSObject
print("\n=== ANALYZING BaseAWSObject VALIDATION ===\n")

print("BaseAWSObject.__setattr__ logic:")
print("- Checks if value is AWSHelperFn and skips validation")
print("- For functions, calls the validator and stores result")
print("- For lists, validates each item")
print("- For simple types, uses isinstance check")

# 5. Look for potential issues
print("\n=== POTENTIAL BUGS IDENTIFIED ===\n")

print("BUG 1: Integer validator type inconsistency")
print("  The integer() validator returns the original value, not int(value)")
print("  This means '123' stays as string '123', not converted to 123")
print("  Impact: Type confusion, possible JSON serialization issues")

print("\nBUG 2: Boolean validator incomplete coverage")  
print("  The boolean() validator has hardcoded list of accepted values")
print("  Missing common variants like 'yes', 'no', 'on', 'off'")
print("  Also case-sensitive for some values")

print("\nBUG 3: Title validation regex")
print("  The title regex is: ^[a-zA-Z0-9]+$")
print("  This rejects empty strings correctly")
print("  But also rejects common CloudFormation resource names with underscores")

print("\nBUG 4: from_dict implementation")
print("  Looking at BaseAWSObject._from_dict:")
print("  - Line 376: is_aws_object = is_aws_object_subclass(prop_type)")
print("  - This function could fail for certain prop_type values")

print("\n=== WRITING MINIMAL BUG REPRODUCTION ===\n")

# Write bug reproduction code
bug_repro = '''#!/usr/bin/env python3
"""Minimal bug reproduction for troposphere.licensemanager."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# BUG: Integer validator doesn't convert string to int
print("BUG DEMONSTRATION: Integer validator type inconsistency")
print("-" * 50)

value = "123"
result = validators.integer(value)
print(f"Input: {value!r} (type: {type(value).__name__})")
print(f"Output: {result!r} (type: {type(result).__name__})")
print(f"Expected: Output should be int type, but it's {type(result).__name__}")

# This can cause issues when the value is used in contexts expecting actual integers
# For example, JSON serialization might treat "123" and 123 differently

# Verification
assert result == "123"  # Still a string!
assert type(result) == str  # Not converted to int!
print("\\nVerified: The integer validator returns a string, not an integer!")
'''

with open('/root/hypothesis-llm/worker_/12/bug_reproduction.py', 'w') as f:
    f.write(bug_repro)

print("Bug reproduction script written to bug_reproduction.py")
print("\n=== ANALYSIS COMPLETE ===")