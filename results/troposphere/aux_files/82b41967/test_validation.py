#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appstream

# Test 1: Create with missing required fields
print("=== Test 1: Missing required fields ===")
s3_missing = appstream.S3Location()
print(f"Created S3Location without fields: {s3_missing.to_dict()}")

# Test 2: Create with extra fields
print("\n=== Test 2: Extra fields ===")
try:
    s3_extra = appstream.S3Location(
        S3Bucket="bucket",
        S3Key="key", 
        InvalidField="value"
    )
    print(f"Created S3Location with extra field: {s3_extra.to_dict()}")
except Exception as e:
    print(f"Error with extra field: {e}")

# Test 3: Wrong types
print("\n=== Test 3: Wrong types ===")
try:
    compute_wrong = appstream.ComputeCapacity(
        DesiredInstances="not_an_integer",
        DesiredSessions=5
    )
    print(f"Created ComputeCapacity with string instead of int: {compute_wrong.to_dict()}")
except Exception as e:
    print(f"Error with wrong type: {e}")

# Test 4: Test validation method if it exists
print("\n=== Test 4: Validation method ===")
s3 = appstream.S3Location(S3Bucket="bucket", S3Key="key")
if hasattr(s3, 'validate'):
    try:
        s3.validate()
        print("Validation passed for complete S3Location")
    except Exception as e:
        print(f"Validation error: {e}")

s3_bad = appstream.S3Location(S3Bucket="bucket")  # Missing S3Key
if hasattr(s3_bad, 'validate'):
    try:
        s3_bad.validate()
        print("Validation passed for incomplete S3Location - UNEXPECTED")
    except Exception as e:
        print(f"Validation error for incomplete: {e}")

# Test 5: Test integer validators
print("\n=== Test 5: Integer validator ===")
from troposphere.validators import integer
print(f"integer(5) = {integer(5)}")
print(f"integer('5') = {integer('5')}")
try:
    print(f"integer('not_a_number') = {integer('not_a_number')}")
except Exception as e:
    print(f"integer validation error: {e}")