#!/usr/bin/env python3
"""Reproduce the bug with required properties not being enforced."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloudtrail as cloudtrail


print("Test 1: Creating Destination without required properties")
print("Expected: Should raise ValueError")
print("Actual: ...")
try:
    dest = cloudtrail.Destination()
    print(f"SUCCESS - Created Destination without any properties!")
    print(f"to_dict() output: {dest.to_dict()}")
except Exception as e:
    print(f"FAILED with error: {e}")

print("\n" + "="*60)

print("\nTest 2: Creating Trail without required properties")
print("Expected: Should raise ValueError")
print("Actual: ...")
try:
    trail = cloudtrail.Trail("TestTrail")
    print(f"SUCCESS - Created Trail without required properties!")
    print(f"to_dict() output: {trail.to_dict()}")
except Exception as e:
    print(f"FAILED with error: {e}")

print("\n" + "="*60)

print("\nTest 3: Creating Trail with only one required property (S3BucketName)")
print("Expected: Should raise ValueError")
print("Actual: ...")
try:
    trail = cloudtrail.Trail("TestTrail", S3BucketName="my-bucket")
    print(f"SUCCESS - Created Trail with only S3BucketName!")
    print(f"to_dict() output: {trail.to_dict()}")
except Exception as e:
    print(f"FAILED with error: {e}")

print("\n" + "="*60)

print("\nTest 4: Calling to_dict() triggers validation")
print("Testing if validation happens during to_dict()...")
try:
    trail = cloudtrail.Trail("TestTrail")
    print("Trail created successfully without required properties")
    trail_dict = trail.to_dict()
    print(f"to_dict() also succeeded: {trail_dict}")
except Exception as e:
    print(f"to_dict() raised error: {e}")

print("\n" + "="*60)

print("\nTest 5: Validation can be disabled")
print("Testing with validation=False...")
try:
    trail = cloudtrail.Trail("TestTrail")
    trail_dict = trail.to_dict(validation=False)
    print(f"to_dict(validation=False) succeeded: {trail_dict}")
except Exception as e:
    print(f"Error even with validation=False: {e}")