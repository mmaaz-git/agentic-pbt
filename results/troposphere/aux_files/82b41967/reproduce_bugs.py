#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import appstream
from troposphere.validators import integer

print("=== Bug 1: Integer validator accepts booleans and floats ===")

# Test with boolean
print("\nTesting integer(False):")
result = integer(False)
print(f"Result: {result} (type: {type(result)})")
print(f"This is unexpected - False should not be accepted as an integer")

print("\nTesting integer(True):")
result = integer(True)  
print(f"Result: {result} (type: {type(result)})")
print(f"This is unexpected - True should not be accepted as an integer")

# Test with float
print("\nTesting integer(0.0):")
result = integer(0.0)
print(f"Result: {result} (type: {type(result)})")
print(f"This is unexpected - 0.0 (float) should not be accepted as an integer")

print("\nTesting integer(3.14):")
result = integer(3.14)
print(f"Result: {result} (type: {type(result)})")
print(f"This is unexpected - 3.14 (float) should not be accepted as an integer")

print("\n=== Bug 2: Tags validator rejects empty dictionary ===")

print("\nTesting empty dictionary as Tags:")
try:
    ab = appstream.AppBlock(
        'TestAppBlock',
        Name='TestBlock',
        SourceS3Location=appstream.S3Location(S3Bucket='bucket', S3Key='key'),
        Tags={}  # Empty dict should be valid for Tags
    )
    print("Created AppBlock with empty Tags dict - Success")
except ValueError as e:
    print(f"Error with empty Tags dict: {e}")
    print("This is a bug - empty dict should be valid for Tags")

print("\nTesting non-empty dictionary as Tags:")
try:
    ab = appstream.AppBlock(
        'TestAppBlock2',
        Name='TestBlock2',
        SourceS3Location=appstream.S3Location(S3Bucket='bucket', S3Key='key'),
        Tags={'key1': 'value1'}
    )
    print("Created AppBlock with non-empty Tags dict - Success")
except ValueError as e:
    print(f"Error with non-empty Tags dict: {e}")
    print("This is a bug - dict should be valid for Tags")