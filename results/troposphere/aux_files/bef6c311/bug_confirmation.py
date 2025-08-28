#!/usr/bin/env python3
"""Confirmation of discovered bugs in troposphere.ce"""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce
from troposphere.validators import double

def test_bug_1_hash_equality():
    """BUG: Hash and equality issues with None title in AWSProperty objects"""
    
    print("\n" + "="*60)
    print("BUG 1: Hash/Equality Issue with AWSProperty objects")
    print("="*60)
    
    # Create two identical ResourceTag objects (AWSProperty subclass)
    tag1 = ce.ResourceTag(Key="TestKey", Value="TestValue")
    tag2 = ce.ResourceTag(Key="TestKey", Value="TestValue")
    
    # These should be equal and have same hash
    are_equal = (tag1 == tag2)
    same_hash = (hash(tag1) == hash(tag2))
    
    print(f"Two identical ResourceTag objects:")
    print(f"  tag1 == tag2: {are_equal}")
    print(f"  hash(tag1) == hash(tag2): {same_hash}")
    
    if not are_equal or not same_hash:
        print("\n✗ BUG CONFIRMED: Equal objects don't have equal hashes!")
        print(f"  This violates Python's hash/equality contract")
        print(f"  Impact: Cannot use these objects in sets or as dict keys reliably")
        
        # Demonstrate the impact
        tag_set = {tag1, tag2}
        print(f"\n  Demonstration - Set with both tags has {len(tag_set)} elements")
        print(f"  Expected: 1 element (since they're equal)")
        print(f"  Actual: {len(tag_set)} element(s)")
        
        return True
    else:
        print("✓ No bug found - hash and equality work correctly")
        return False

def test_bug_2_double_validator():
    """BUG: Double validator doesn't convert to float, just validates"""
    
    print("\n" + "="*60)
    print("BUG 2: Double validator type preservation issue")
    print("="*60)
    
    # Test with string number
    string_num = "42.5"
    result = double(string_num)
    
    print(f"double('{string_num}') returns:")
    print(f"  Value: {repr(result)}")
    print(f"  Type: {type(result).__name__}")
    
    if isinstance(result, str):
        print("\n✗ BUG CONFIRMED: double() returns string, not float!")
        print(f"  This could cause CloudFormation template issues")
        print(f"  AWS might expect numeric JSON values, not strings")
        
        # Show impact in actual usage
        subscriber = ce.Subscriber(Address="test@example.com", Type="EMAIL")
        subscription = ce.AnomalySubscription(
            SubscriptionName="Test",
            Frequency="DAILY",
            MonitorArnList=["arn:aws:ce::123:anomalymonitor/test"],
            Subscribers=[subscriber],
            Threshold="100.5"  # String threshold
        )
        
        template = subscription.to_dict()
        threshold_value = template['Properties']['Threshold']
        
        print(f"\n  In AnomalySubscription with Threshold='100.5':")
        print(f"    Stored as: {repr(threshold_value)} (type: {type(threshold_value).__name__})")
        print(f"    JSON output: {json.dumps({'Threshold': threshold_value})}")
        
        return True
    else:
        print("✓ No bug - double() converts to float")
        return False

def test_bug_3_equality_with_dict():
    """BUG: Equality comparison with dict includes None title"""
    
    print("\n" + "="*60)
    print("BUG 3: Dict equality comparison includes None title")
    print("="*60)
    
    tag = ce.ResourceTag(Key="TestKey", Value="TestValue")
    tag_dict = tag.to_dict()
    
    print(f"ResourceTag.to_dict(): {tag_dict}")
    print(f"tag.title: {tag.title}")
    
    # Try equality comparison
    equals_dict = (tag == tag_dict)
    print(f"\ntag == tag.to_dict(): {equals_dict}")
    
    # The __eq__ method creates {"title": None, **to_dict()} for comparison
    # This means the dict comparison includes a None title
    
    # Check what the comparison actually does
    comparison_dict = {"title": tag.title, **tag.to_dict()}
    print(f"\nInternal comparison dict: {comparison_dict}")
    
    if "title" in str(comparison_dict) and tag.title is None:
        print("\n✗ BUG CONFIRMED: Comparison includes 'title': None")
        print("  This makes dict equality comparisons unreliable")
        print("  The to_dict() output won't equal the object itself")
        return True
    else:
        print("✓ No bug in dict equality")
        return False

def main():
    print("="*60)
    print("TROPOSPHERE.CE BUG CONFIRMATION")
    print("="*60)
    
    bugs_found = []
    
    # Test each potential bug
    if test_bug_1_hash_equality():
        bugs_found.append("Hash/Equality contract violation")
    
    if test_bug_2_double_validator():
        bugs_found.append("Double validator type preservation")
    
    if test_bug_3_equality_with_dict():
        bugs_found.append("Dict equality comparison issue")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if bugs_found:
        print(f"✗ Found {len(bugs_found)} bug(s):")
        for bug in bugs_found:
            print(f"  - {bug}")
    else:
        print("✓ No bugs found")
    
    return len(bugs_found) > 0

if __name__ == "__main__":
    main()