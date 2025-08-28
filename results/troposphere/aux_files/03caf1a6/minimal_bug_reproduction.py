#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.fis as fis

# Minimal reproduction of the bug
print("Bug: Optional properties with None value fail during object creation")
print("="*60)

# This works - omitting optional property
config1 = fis.ExperimentReportS3Configuration(BucketName="test-bucket")
dict1 = config1.to_dict()
print(f"✓ Without optional property works: {dict1}")

# This fails - explicitly setting optional property to None
try:
    config2 = fis.ExperimentReportS3Configuration(
        BucketName="test-bucket",
        Prefix=None
    )
    print("✓ With Prefix=None works")
except TypeError as e:
    print(f"✗ With Prefix=None fails: {e}")

# This also fails - round-trip with None in dict
try:
    test_dict = {"BucketName": "test-bucket", "Prefix": None}
    config3 = fis.ExperimentReportS3Configuration._from_dict(**test_dict)
    print("✓ from_dict with None works")
except TypeError as e:
    print(f"✗ from_dict with None fails: {e}")

print("\nExpected behavior: None should be allowed for optional properties")