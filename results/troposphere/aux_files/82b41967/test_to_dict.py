#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appstream

print("=== Test: to_dict triggers validation ===")

# Test 1: Missing required field
s3_missing = appstream.S3Location()
print("Created S3Location without required fields")
try:
    result = s3_missing.to_dict()
    print(f"to_dict succeeded unexpectedly: {result}")
except ValueError as e:
    print(f"to_dict validation error (expected): {e}")

# Test 2: Partial required fields
s3_partial = appstream.S3Location(S3Bucket="bucket")
print("\nCreated S3Location with only S3Bucket")
try:
    result = s3_partial.to_dict()
    print(f"to_dict succeeded unexpectedly: {result}")
except ValueError as e:
    print(f"to_dict validation error (expected): {e}")

# Test 3: All required fields
s3_complete = appstream.S3Location(S3Bucket="bucket", S3Key="key")
print("\nCreated S3Location with all required fields")
try:
    result = s3_complete.to_dict()
    print(f"to_dict succeeded: {result}")
except ValueError as e:
    print(f"to_dict validation error (unexpected): {e}")

# Test 4: Check that validation can be disabled
print("\n=== Test: Validation flag ===")
ab = appstream.AppBlock("TestBlock", validation=False)
print("Created AppBlock with validation=False and no required fields")
try:
    result = ab.to_dict()
    print(f"to_dict result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Integer fields
print("\n=== Test: Integer fields ===")
compute = appstream.ComputeCapacity(DesiredInstances="5")  # String instead of int
print("Created ComputeCapacity with string '5' for integer field")
try:
    result = compute.to_dict()
    print(f"to_dict result: {result}")
except Exception as e:
    print(f"Error: {e}")