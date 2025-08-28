#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appstream

# Test creation and to_dict round-trip
s3 = appstream.S3Location(S3Bucket="test-bucket", S3Key="test-key")
print("S3Location to_dict:", s3.to_dict())

# Test with all property types
compute = appstream.ComputeCapacity(DesiredInstances=5, DesiredSessions=10)
print("ComputeCapacity to_dict:", compute.to_dict())

# Test required vs optional fields
try:
    bad_s3 = appstream.S3Location()
    print("Created S3Location without required fields - UNEXPECTED")
except TypeError as e:
    print(f"Expected error for missing required fields: {e}")

# Test nested properties
ab = appstream.AppBlock(
    "TestBlock",
    Name="MyBlock",
    SourceS3Location=s3
)
print("AppBlock resource_type:", ab.resource_type)

# Check the to_dict method on AWSObject
print("AppBlock to_dict keys:", list(ab.to_dict().keys()))