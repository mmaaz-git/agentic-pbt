#!/usr/bin/env python3
"""Test for double validator behavior"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import double
import troposphere.ce as ce

print("=" * 50)
print("Testing double validator behavior")
print("=" * 50)

# The double validator code (from reading the source):
# def double(x):
#     try:
#         float(x)
#     except (ValueError, TypeError):
#         raise ValueError("%r is not a valid double" % x)
#     else:
#         return x  # <-- Returns original value, not the float!

test_cases = [
    ("42", "String number"),
    (42, "Integer"),
    (42.5, "Float"),
    ("  42  ", "Number with spaces"),
    ("42.0", "String float"),
    (True, "Boolean True"),
    (False, "Boolean False"),
]

print("\n1. Testing double validator return values:")
for value, description in test_cases:
    try:
        result = double(value)
        print(f"  {description}: double({repr(value)}) = {repr(result)}")
        print(f"    Type of input:  {type(value).__name__}")
        print(f"    Type of output: {type(result).__name__}")
        
        # Check if types are preserved
        if type(value) != type(result):
            print(f"    ✗ BUG: Type changed from {type(value).__name__} to {type(result).__name__}")
        else:
            print(f"    ✓ Type preserved")
            
    except Exception as e:
        print(f"  {description}: Failed with {e}")

print("\n2. Testing in AnomalySubscription:")
# Create a subscription with string threshold
subscriber = ce.Subscriber(Address="test@example.com", Type="EMAIL")

test_thresholds = ["100.5", 100.5, "100", 100]

for threshold in test_thresholds:
    print(f"\n  Testing threshold={repr(threshold)} (type: {type(threshold).__name__})")
    
    subscription = ce.AnomalySubscription(
        SubscriptionName="TestSub",
        Frequency="DAILY",
        MonitorArnList=["arn:aws:ce::123456789012:anomalymonitor/test"],
        Subscribers=[subscriber],
        Threshold=threshold
    )
    
    result = subscription.to_dict()
    stored_threshold = result['Properties']['Threshold']
    
    print(f"    Stored value: {repr(stored_threshold)}")
    print(f"    Stored type: {type(stored_threshold).__name__}")
    
    # Check if the stored value matches input
    if stored_threshold == threshold:
        print(f"    ✓ Value preserved exactly")
    else:
        print(f"    ✗ Value changed from {repr(threshold)} to {repr(stored_threshold)}")
    
    # Check if type is preserved
    if type(stored_threshold) == type(threshold):
        print(f"    ✓ Type preserved")
    else:
        print(f"    Note: Type changed from {type(threshold).__name__} to {type(stored_threshold).__name__}")

print("\n" + "=" * 50)
print("Analysis:")
print("=" * 50)
print("The double validator accepts values that can be converted to float")
print("but returns the ORIGINAL value, not the converted float.")
print("This means '100.5' stays as a string, not converted to 100.5")
print("This could cause issues if AWS CloudFormation expects actual numeric values.")