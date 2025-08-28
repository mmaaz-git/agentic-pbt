#!/usr/bin/env python3
"""Test type validation behavior in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloudtrail as cloudtrail

print("Testing type validation at object creation time:")
print("="*60)

print("\n1. Setting boolean field to invalid value:")
try:
    trail = cloudtrail.Trail("TestTrail", 
                           S3BucketName="my-bucket",
                           IsLogging="not-a-boolean")
    print(f"  ✗ Created Trail with IsLogging='not-a-boolean'")
    try:
        trail.to_dict()
        print(f"  ✗✗ to_dict() also succeeded!")
    except Exception as e:
        print(f"  ✓ to_dict() caught it: {e}")
except Exception as e:
    print(f"  ✓ Rejected at creation: {e}")

print("\n2. Setting integer field to non-integer:")
try:
    freq = cloudtrail.Frequency(Unit="HOURS", Value="not-an-integer")
    print(f"  ✗ Created Frequency with Value='not-an-integer'")
    try:
        freq.to_dict()
        print(f"  ✗✗ to_dict() also succeeded!")
    except Exception as e:
        print(f"  ✓ to_dict() caught it: {e}")
except Exception as e:
    print(f"  ✓ Rejected at creation: {e}")

print("\n3. Setting positive integer field to negative value:")
try:
    store = cloudtrail.EventDataStore("TestStore", RetentionPeriod=-100)
    print(f"  ✗ Created EventDataStore with RetentionPeriod=-100")
    print(f"  Properties: {store.properties}")
    try:
        store_dict = store.to_dict()
        print(f"  ✗✗ to_dict() succeeded with negative retention: {store_dict}")
    except Exception as e:
        print(f"  ✓ to_dict() caught it: {e}")
except Exception as e:
    print(f"  ✓ Rejected at creation: {e}")

print("\n4. Setting list field to non-list:")
try:
    selector = cloudtrail.AdvancedEventSelector(
        FieldSelectors="not-a-list"
    )
    print(f"  ✗ Created AdvancedEventSelector with FieldSelectors as string")
    try:
        selector.to_dict()
        print(f"  ✗✗ to_dict() also succeeded!")
    except Exception as e:
        print(f"  ✓ to_dict() caught it: {e}")
except Exception as e:
    print(f"  ✓ Rejected at creation: {e}")

print("\n5. Boolean accepts string 'true' and 'false':")
try:
    trail1 = cloudtrail.Trail("Trail1", 
                            S3BucketName="bucket",
                            IsLogging="true")
    print(f"  Created Trail with IsLogging='true'")
    print(f"  Value stored: {trail1.IsLogging}")
    trail1_dict = trail1.to_dict()
    print(f"  to_dict() result: {trail1_dict['Properties']['IsLogging']}")
except Exception as e:
    print(f"  Error: {e}")

print("\n6. Integer validator accepts string numbers:")
try:
    freq = cloudtrail.Frequency(Unit="HOURS", Value="42")
    print(f"  Created Frequency with Value='42' (string)")
    print(f"  Value stored: {freq.Value} (type: {type(freq.Value).__name__})")
    freq_dict = freq.to_dict()
    print(f"  to_dict() result: {freq_dict}")
except Exception as e:
    print(f"  Error: {e}")