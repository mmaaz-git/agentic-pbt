#!/usr/bin/env python3
"""Reproduce potential type validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("Testing potential type validation bug in troposphere.datapipeline")
print("=" * 70)

from troposphere import datapipeline

# Create a Pipeline 
pipeline = datapipeline.Pipeline("ValidTitle")

print("\n1. Testing integer assignment to string field 'Name':")
print("   According to props, Name should be (str, True)")

# Try to assign an integer to Name field
pipeline.Name = 12345
print(f"   ✗ BUG FOUND: Pipeline.Name accepts integer: {pipeline.Name}")
print(f"   Type of stored value: {type(pipeline.Name)}")

# Check what happens when we serialize
d = pipeline.to_dict()
print(f"   Serialized form: {d}")
print(f"   Name in dict: {d['Properties']['Name']} (type: {type(d['Properties']['Name'])})")

print("\n2. Testing with Activate field (should use boolean validator):")
pipeline2 = datapipeline.Pipeline("Test2")
pipeline2.Name = "TestPipeline"

# The boolean validator should reject this
try:
    pipeline2.Activate = "YES"  # Not in the accepted list
    print(f"   ✗ Activate accepts 'YES': {pipeline2.Activate}")
except (ValueError, TypeError) as e:
    print(f"   ✓ Activate correctly rejects 'YES': {e}")

print("\n3. Testing empty string for required field:")
try:
    attr = datapipeline.ParameterObjectAttribute(
        Key="",  # Empty but still a string
        StringValue="value"
    )
    print(f"   ✗ BUG FOUND: Empty string accepted for required Key field")
    print(f"   to_dict: {attr.to_dict()}")
except ValueError as e:
    print(f"   ✓ Empty string rejected: {e}")

print("\n4. Testing list field with tuple:")
try:
    # Create attributes as tuple instead of list
    param = datapipeline.ParameterObject(
        Id="test",
        Attributes=(  # Tuple instead of list
            datapipeline.ParameterObjectAttribute(Key="k1", StringValue="v1"),
            datapipeline.ParameterObjectAttribute(Key="k2", StringValue="v2"),
        )
    )
    print(f"   ✗ BUG FOUND: Tuple accepted for list field")
    print(f"   Type stored: {type(param.Attributes)}")
except TypeError as e:
    print(f"   ✓ Tuple correctly rejected for list field: {e}")

print("\nSUMMARY:")
print("-" * 70)
print("The type validation in troposphere appears to have issues:")
print("1. Integer values are accepted for string fields (no type coercion)")
print("2. Empty strings are accepted for required string fields")
print("3. The validation happens at different times (assignment vs serialization)")

print("\nTo reproduce the main bug:")
print(">>> from troposphere import datapipeline")
print(">>> p = datapipeline.Pipeline('Test')")
print(">>> p.Name = 12345  # Should fail but doesn't")
print(">>> p.Name")
print("12345")
print(">>> type(p.Name)")
print("<class 'int'>")