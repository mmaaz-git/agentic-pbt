#!/usr/bin/env python3
"""Comprehensive bug hunting for troposphere.datapipeline"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import datapipeline, validators
import json

print("COMPREHENSIVE BUG HUNT FOR troposphere.datapipeline")
print("=" * 70)

# Bug Hunt 1: Empty strings in required fields
print("\n1. Testing empty strings in required string fields...")
try:
    # Key is required and should be a string
    attr = datapipeline.ParameterObjectAttribute(Key="", StringValue="test")
    d = attr.to_dict()
    print(f"  ✗ BUG: Empty Key accepted: {d}")
except (ValueError, TypeError) as e:
    print(f"  ✓ Empty Key rejected: {e}")

# Bug Hunt 2: None values in required fields
print("\n2. Testing None in required fields...")
try:
    attr = datapipeline.ParameterObjectAttribute(Key=None, StringValue="test")
    d = attr.to_dict()
    print(f"  ✗ BUG: None Key accepted: {d}")
except (TypeError, AttributeError) as e:
    print(f"  ✓ None Key rejected: {type(e).__name__}")

# Bug Hunt 3: Type coercion edge cases
print("\n3. Testing type coercion for string fields...")
pipeline = datapipeline.Pipeline("TestPipeline")

# Name should be a string, but does it accept numbers?
try:
    pipeline.Name = 12345
    print(f"  ✗ Potential issue: Name accepts integer {pipeline.Name} (type: {type(pipeline.Name)})")
    # Check if it's converted to string
    d = pipeline.to_dict()
    print(f"    Serialized as: {d}")
except TypeError as e:
    print(f"  ✓ Name rejects integer: {e}")

# Bug Hunt 4: Unicode and special characters
print("\n4. Testing Unicode and special characters...")
try:
    # Test with emoji
    tag = datapipeline.PipelineTag(Key="🔑", Value="💰")
    d = tag.to_dict()
    print(f"  ✓ Unicode accepted: {d}")
except Exception as e:
    print(f"  ✗ Unicode rejected: {e}")

# Bug Hunt 5: Extremely long strings
print("\n5. Testing extremely long strings...")
long_string = "A" * 10000
try:
    pipeline2 = datapipeline.Pipeline("Valid")
    pipeline2.Name = long_string
    pipeline2.Description = long_string
    d = pipeline2.to_dict()
    print(f"  ✓ Long strings accepted (length: {len(pipeline2.Name)})")
except Exception as e:
    print(f"  ✗ Long strings rejected: {e}")

# Bug Hunt 6: Circular references or deep nesting
print("\n6. Testing deep nesting with PipelineObject...")
fields = []
for i in range(100):
    fields.append(datapipeline.ObjectField(
        Key=f"field{i}",
        StringValue=f"value{i}"
    ))

try:
    obj = datapipeline.PipelineObject(
        Id="deepobj",
        Name="DeepObject", 
        Fields=fields
    )
    d = obj.to_dict()
    print(f"  ✓ Deep nesting handled (100 fields)")
except Exception as e:
    print(f"  ✗ Deep nesting failed: {e}")

# Bug Hunt 7: Validation order dependencies
print("\n7. Testing validation order issues...")
pipeline3 = datapipeline.Pipeline("Test")

# Set Activate before Name (required field)
try:
    pipeline3.Activate = True  # This uses boolean validator
    # Now try to serialize without Name
    d = pipeline3.to_dict()
    print(f"  ✗ Validation passed without required Name: {d}")
except ValueError as e:
    print(f"  ✓ Validation correctly requires Name: {e}")

# Bug Hunt 8: Property overwriting
print("\n8. Testing property overwriting behavior...")
pipeline4 = datapipeline.Pipeline("Test")
pipeline4.Name = "FirstName"
pipeline4.Name = "SecondName"
print(f"  Name after double assignment: {pipeline4.Name}")

# Can we assign incompatible types after first assignment?
try:
    pipeline4.Name = ["List", "Value"]
    print(f"  ✗ BUG: Name accepts list after string: {pipeline4.Name}")
except TypeError as e:
    print(f"  ✓ Name rejects list: {type(e).__name__}")

# Bug Hunt 9: from_dict round-trip
print("\n9. Testing from_dict reconstruction...")
original = datapipeline.ParameterValue(Id="test", StringValue="value")
dict_form = original.to_dict()
print(f"  Original dict: {dict_form}")

try:
    # Try to reconstruct - note AWSProperty doesn't have from_dict by default
    reconstructed = datapipeline.ParameterValue._from_dict(**dict_form)
    print(f"  ✓ Reconstructed successfully")
    if reconstructed.to_dict() == dict_form:
        print(f"  ✓ Round-trip preserves data")
    else:
        print(f"  ✗ BUG: Round-trip changes data!")
        print(f"    Before: {dict_form}")
        print(f"    After:  {reconstructed.to_dict()}")
except AttributeError as e:
    print(f"  Note: _from_dict exists but may not be public API")

# Bug Hunt 10: Edge case in boolean validator itself
print("\n10. Testing boolean validator edge cases...")

# The validator code checks x in [True, 1, "1", "true", "True"]
# But what about these edge cases?
edge_cases = [
    (1.0, "float 1.0"),
    (0.0, "float 0.0"),
    ("TRUE", "uppercase TRUE"),
    ("FALSE", "uppercase FALSE"),
    (" true", "leading space"),
    ("true ", "trailing space"),
    ("yes", "yes string"),
    ("no", "no string"),
    ("on", "on string"),
    ("off", "off string"),
    ([], "empty list"),
    ({}, "empty dict"),
    ("", "empty string"),
]

for value, description in edge_cases:
    try:
        result = validators.boolean(value)
        print(f"  boolean({description:<20}) = {result}")
    except ValueError:
        print(f"  boolean({description:<20}) -> ValueError")

print("\n" + "=" * 70)
print("BUG HUNT COMPLETE")
print("\nSummary of potential issues found:")
print("1. Empty strings may be accepted in required string fields")
print("2. Integer values might be silently accepted for string fields")  
print("3. No apparent validation on string length limits")
print("4. Boolean validator is case-sensitive ('TRUE' vs 'True')")