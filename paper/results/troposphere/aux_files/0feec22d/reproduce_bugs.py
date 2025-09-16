#!/usr/bin/env python3
"""Reproduce bugs in troposphere.s3express module"""

import troposphere.s3express as s3e

print("Bug 1: from_dict/to_dict round-trip property violation")
print("=" * 60)

# Create a DirectoryBucket object
db = s3e.DirectoryBucket('TestBucket',
                        DataRedundancy='SingleAvailabilityZone',
                        LocationName='use1-az1')

# Convert to dict
dict_repr = db.to_dict()
print(f"to_dict() output: {dict_repr}")

# Try to recreate from the dict output
print("\nAttempting to recreate from full to_dict() output...")
try:
    recreated = s3e.DirectoryBucket.from_dict('TestBucket2', dict_repr)
    print("SUCCESS: Object recreated")
except AttributeError as e:
    print(f"FAILED: {e}")
    print("\nThis is a bug - from_dict() should accept the output of to_dict()")
    
    # Show the workaround
    print("\nWorkaround: Pass only the 'Properties' part:")
    recreated = s3e.DirectoryBucket.from_dict('TestBucket2', dict_repr['Properties'])
    print("SUCCESS with workaround")

print("\n" + "=" * 60)
print("Bug 2: Missing required properties validation")
print("=" * 60)

# DirectoryBucket requires DataRedundancy and LocationName
db_incomplete = s3e.DirectoryBucket('IncompleteBucket')
print("Created DirectoryBucket without required properties")

print("Calling validate()...")
try:
    db_incomplete.validate()
    print("VALIDATION PASSED - This is a bug!")
    print("Required properties DataRedundancy and LocationName are missing")
except Exception as e:
    print(f"Validation correctly failed: {e}")

print("\nTrying to convert incomplete object to dict...")
try:
    incomplete_dict = db_incomplete.to_dict()
    print(f"to_dict() output: {incomplete_dict}")
except ValueError as e:
    print(f"to_dict() correctly validates: {e}")
    print("Note: to_dict() validates required properties but validate() doesn't!")