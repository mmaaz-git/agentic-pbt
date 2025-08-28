#!/usr/bin/env python3
"""Simple test to check troposphere.ce for bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce
from troposphere.validators import double

print("Testing troposphere.ce module...")

# Test 1: Basic ResourceTag functionality
print("\n1. Testing ResourceTag creation...")
try:
    tag = ce.ResourceTag(Key="TestKey", Value="TestValue")
    print(f"   Created tag: {tag.to_dict()}")
    print("   ✓ ResourceTag works")
except Exception as e:
    print(f"   ✗ ResourceTag failed: {e}")

# Test 2: Missing required property
print("\n2. Testing missing required property...")
try:
    tag = ce.ResourceTag(Key="TestKey")  # Missing Value
    result = tag.to_dict()  # This should trigger validation
    print(f"   ✗ BUG: Should have failed but got: {result}")
except (ValueError, TypeError) as e:
    print(f"   ✓ Correctly raised error: {e}")

# Test 3: Double validator
print("\n3. Testing double validator...")
test_values = [
    (3.14, True),
    (42, True),
    ("3.14", True),
    ("42", True),
    ("not_a_number", False),
    ([], False),
    ({}, False),
]

for value, should_pass in test_values:
    try:
        result = double(value)
        if should_pass:
            print(f"   ✓ double({repr(value)}) = {result}")
        else:
            print(f"   ✗ BUG: double({repr(value)}) should have failed but returned {result}")
    except (ValueError, TypeError) as e:
        if not should_pass:
            print(f"   ✓ double({repr(value)}) correctly raised error")
        else:
            print(f"   ✗ BUG: double({repr(value)}) should have passed but raised {e}")

# Test 4: AnomalySubscription with threshold
print("\n4. Testing AnomalySubscription with Threshold...")
try:
    subscriber = ce.Subscriber(Address="test@example.com", Type="EMAIL")
    subscription = ce.AnomalySubscription(
        SubscriptionName="TestSub",
        Frequency="DAILY",
        MonitorArnList=["arn:aws:ce:us-east-1:123456789012:anomalymonitor/test"],
        Subscribers=[subscriber],
        Threshold=100.5
    )
    result = subscription.to_dict()
    print(f"   ✓ Created subscription with threshold: {result['Properties']['Threshold']}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 5: Edge cases with empty strings
print("\n5. Testing empty string handling...")
try:
    tag = ce.ResourceTag(Key="", Value="test")
    result = tag.to_dict()
    # Empty strings might be allowed, depends on AWS validation
    print(f"   Note: Empty string accepted, result: {result}")
except Exception as e:
    print(f"   Empty string rejected: {e}")

# Test 6: Property access
print("\n6. Testing property access patterns...")
try:
    tag = ce.ResourceTag(Key="MyKey", Value="MyValue")
    
    # Test direct property access
    assert tag.Key == "MyKey"
    assert tag.Value == "MyValue"
    print("   ✓ Direct property access works")
    
    # Test dictionary conversion
    d = tag.to_dict()
    assert d['Key'] == "MyKey"
    assert d['Value'] == "MyValue"
    print("   ✓ to_dict() conversion works")
    
except Exception as e:
    print(f"   ✗ Property access failed: {e}")

# Test 7: Test with special characters
print("\n7. Testing special characters in strings...")
special_strings = [
    "normal",
    "with spaces",
    "with-dashes",
    "with_underscores",
    "with.dots",
    "with/slashes",
    "with\\backslashes",
    "with'quotes",
    'with"doublequotes',
    "with\ttabs",
    "with\nnewlines",
    "😀emoji",
    "",  # empty
]

for s in special_strings:
    try:
        tag = ce.ResourceTag(Key=s if s else "key", Value=s if s else "value")
        result = tag.to_dict()
        if s:
            print(f"   ✓ Handled {repr(s)}: Key={result.get('Key')}, Value={result.get('Value')}")
        else:
            print(f"   ✓ Handled empty string")
    except Exception as e:
        print(f"   Note: String {repr(s)} rejected: {e}")

print("\n=== Testing Complete ===")