#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.fis as fis

# Test the specific failing case
bucket_name = "test-bucket"
prefix = ""  # Empty string from hypothesis

print("Testing with empty prefix...")
try:
    # Create nested structure with empty prefix
    s3_config = fis.ExperimentReportS3Configuration(
        BucketName=bucket_name,
        Prefix=None  # Setting to None when prefix is empty
    )
    print(f"Created S3Configuration with Prefix=None")
    
    # Check the properties
    print(f"Properties: {s3_config.properties}")
    
    # Convert to dict
    dict_repr = s3_config.to_dict()
    print(f"Dict representation: {dict_repr}")
    
    # Try to recreate from dict
    s3_config2 = fis.ExperimentReportS3Configuration._from_dict(**dict_repr)
    print("Successfully recreated from dict")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")

print("\n" + "="*50)
print("Testing handling of None vs omitted optional properties...")

# Test 1: Explicitly passing None
print("\nTest 1: Explicitly passing Prefix=None")
try:
    config1 = fis.ExperimentReportS3Configuration(
        BucketName="bucket1",
        Prefix=None
    )
    print(f"Properties with explicit None: {config1.properties}")
    dict1 = config1.to_dict()
    print(f"Dict with explicit None: {dict1}")
except Exception as e:
    print(f"Failed with explicit None: {e}")

# Test 2: Not passing Prefix at all
print("\nTest 2: Not passing Prefix at all")
try:
    config2 = fis.ExperimentReportS3Configuration(
        BucketName="bucket2"
    )
    print(f"Properties without Prefix: {config2.properties}")
    dict2 = config2.to_dict()
    print(f"Dict without Prefix: {dict2}")
except Exception as e:
    print(f"Failed without Prefix: {e}")

# Test 3: Round-trip with None
print("\nTest 3: Round-trip with None in dict")
try:
    original_dict = {"BucketName": "bucket3", "Prefix": None}
    print(f"Original dict: {original_dict}")
    
    recreated = fis.ExperimentReportS3Configuration._from_dict(**original_dict)
    print(f"Recreated properties: {recreated.properties}")
    new_dict = recreated.to_dict()
    print(f"New dict: {new_dict}")
    
    if original_dict == new_dict:
        print("✓ Round-trip successful")
    else:
        print("✗ Round-trip failed - dicts don't match")
        
except Exception as e:
    print(f"Round-trip failed: {e}")