#!/usr/bin/env python3
"""Manual testing for troposphere.datapipeline bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import datapipeline, validators

print("Testing boolean validator edge cases...")

# Test 1: Check if "1" string is handled correctly
try:
    result = validators.boolean("1")
    print(f"✓ boolean('1') = {result}")
except Exception as e:
    print(f"✗ boolean('1') failed: {e}")

# Test 2: Check if integer 1 is handled correctly  
try:
    result = validators.boolean(1)
    print(f"✓ boolean(1) = {result}")
except Exception as e:
    print(f"✗ boolean(1) failed: {e}")

# Test 3: Check if "0" string is handled correctly
try:
    result = validators.boolean("0")
    print(f"✓ boolean('0') = {result}")
except Exception as e:
    print(f"✗ boolean('0') failed: {e}")

# Test 4: Check Pipeline required field validation
print("\nTesting Pipeline required field validation...")
try:
    pipeline = datapipeline.Pipeline("TestPipeline")
    # Don't set Name (which is required)
    result = pipeline.to_dict()
    print(f"✗ Pipeline without Name should fail validation but got: {result}")
except ValueError as e:
    print(f"✓ Pipeline without Name correctly raises: {e}")

# Test 5: Check if empty string title is accepted
print("\nTesting title validation...")
try:
    pipeline = datapipeline.Pipeline("")
    print(f"✗ Empty title should fail but was accepted")
except ValueError as e:
    print(f"✓ Empty title correctly raises: {e}")

# Test 6: Check if title with special characters is rejected
try:
    pipeline = datapipeline.Pipeline("Test-Pipeline")
    print(f"✗ Title with hyphen should fail but was accepted")
except ValueError as e:
    print(f"✓ Title with hyphen correctly raises: {e}")

# Test 7: Check ObjectField with both RefValue and StringValue
print("\nTesting ObjectField properties...")
try:
    field = datapipeline.ObjectField(
        Key="testkey",
        RefValue="ref",
        StringValue="string"
    )
    d = field.to_dict()
    print(f"✓ ObjectField with both values: {d}")
except Exception as e:
    print(f"✗ ObjectField failed: {e}")

# Test 8: Check Pipeline.Activate with boolean validator
print("\nTesting Pipeline.Activate boolean property...")
pipeline = datapipeline.Pipeline("ValidPipeline")
pipeline.Name = "TestPipeline"

test_values = [True, False, 1, 0, "1", "0", "true", "false", "True", "False", 
               2, -1, "yes", "no", "TRUE", "FALSE", None, [], {}]

for val in test_values:
    try:
        pipeline.Activate = val
        print(f"✓ Activate={val} -> {pipeline.Activate}")
    except (TypeError, ValueError) as e:
        print(f"✗ Activate={val} rejected: {type(e).__name__}")

# Test 9: Check ParameterObject with empty Attributes list
print("\nTesting ParameterObject with edge cases...")
try:
    param = datapipeline.ParameterObject(
        Id="test",
        Attributes=[]  # Empty list
    )
    d = param.to_dict()
    print(f"✓ ParameterObject with empty Attributes: {d}")
except Exception as e:
    print(f"✗ ParameterObject with empty Attributes failed: {e}")

# Test 10: Test type coercion/validation
print("\nTesting type validation edge cases...")
pipeline2 = datapipeline.Pipeline("Pipeline2")
try:
    pipeline2.Name = 123  # Should this be accepted?
    print(f"✗ Pipeline.Name accepted integer 123: {pipeline2.Name}")
except TypeError as e:
    print(f"✓ Pipeline.Name correctly rejects integer: {e}")