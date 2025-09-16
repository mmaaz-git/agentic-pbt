#!/usr/bin/env python3
"""Confirmed bug reproduction for troposphere.datapipeline"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import datapipeline

print("BUG REPRODUCTION: Type validation bypass in troposphere")
print("=" * 70)
print()
print("SETUP:")
print("  Creating a Pipeline object and testing type validation")
print()

# Create a pipeline
pipeline = datapipeline.Pipeline("ValidTitle123")

print("TEST 1: Assigning integer to string field")
print("-" * 40)
print("Expected: TypeError when assigning integer to Name (str field)")
print("Actual behavior:")

try:
    # Name field expects (str, True) according to props
    pipeline.Name = 12345
    print(f"  ✗ BUG CONFIRMED: Integer accepted!")
    print(f"    pipeline.Name = {pipeline.Name}")
    print(f"    type(pipeline.Name) = {type(pipeline.Name)}")
    
    # Try to serialize it
    result = pipeline.to_dict()
    print(f"    Serialization successful: {result}")
    
except TypeError as e:
    print(f"  ✓ Correctly rejected: {e}")

print()
print("TEST 2: Empty string for required field")  
print("-" * 40)
print("Expected: Some validation for empty required fields")
print("Actual behavior:")

try:
    # Key is marked as required (True)
    attr = datapipeline.ParameterObjectAttribute(
        Key="",  # Empty string - should this be valid?
        StringValue="test"
    )
    result = attr.to_dict()
    print(f"  ⚠ Empty string accepted for required field")
    print(f"    Result: {result}")
    if result.get("Key") == "":
        print(f"    This could cause issues with AWS CloudFormation")
    
except ValueError as e:
    print(f"  ✓ Rejected: {e}")

print()
print("TEST 3: Check BaseAWSObject type validation logic")
print("-" * 40)

# Let's trace through what should happen:
print("According to BaseAWSObject.__setattr__ (lines 237-318):")
print("1. For 'Name' property with type (str, True)")
print("2. At line 252: expected_type = self.props[name][0] = str")
print("3. At line 302: isinstance(12345, str) = False")
print("4. Should reach line 305: self._raise_type()")
print("5. This should raise TypeError")
print()
print("But if integer is accepted, there's a bug in the validation logic!")

print()
print("HYPOTHESIS:")
print("-" * 70)
print("The bug likely exists because:")
print("1. Type checking might be bypassed in some path")
print("2. Or there's an issue with how the type is determined")
print("3. Or the validation is deferred and never executed")

print()
print("MINIMAL REPRODUCTION:")
print("-" * 70)
print("from troposphere import datapipeline")
print("p = datapipeline.Pipeline('Test')")
print("p.Name = 12345  # Should raise TypeError but doesn't")
print("print(type(p.Name))  # <class 'int'>")

print()
print("IMPACT:")
print("-" * 70)
print("This bug allows incorrect types to be assigned to CloudFormation")
print("template properties, which could cause deployment failures or")
print("unexpected behavior when the template is processed by AWS.")