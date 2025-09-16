#!/usr/bin/env python3
"""Bug hunting script for troposphere.ce"""

import sys
import os

# Set up environment
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
os.chdir('/root/hypothesis-llm/worker_/4')

import troposphere.ce as ce
from troposphere.validators import double
import json

def test_1_property_override_bug():
    """Test if properties can be overridden incorrectly"""
    print("\n=== Test 1: Property Override ===")
    
    # Create a ResourceTag
    tag = ce.ResourceTag(Key="InitialKey", Value="InitialValue")
    
    # Try to override the Key property
    tag.Key = "ModifiedKey"
    
    # Check if modification worked
    result = tag.to_dict()
    print(f"After modification: {result}")
    
    if result['Key'] != "ModifiedKey":
        print("✗ BUG: Property modification didn't work correctly")
        return False
    
    print("✓ Property modification works correctly")
    return True

def test_2_validation_bypass():
    """Test if validation can be bypassed"""
    print("\n=== Test 2: Validation Bypass ===")
    
    # Try to create object without validation
    try:
        # Create without required property
        monitor = ce.AnomalyMonitor()
        monitor.MonitorType = "DIMENSIONAL"
        # Don't set MonitorName (required)
        
        # Try no_validation method if it exists
        if hasattr(monitor, 'no_validation'):
            monitor.no_validation()
            result = monitor.to_dict(validation=False)
            print(f"✗ BUG: Created invalid object without MonitorName: {result}")
            return False
        else:
            result = monitor.to_dict()
            print(f"✗ BUG: Should have failed but got: {result}")
            return False
    except Exception as e:
        print(f"✓ Validation correctly enforced: {e}")
        return True

def test_3_double_validator_edge_cases():
    """Test edge cases in double validator"""
    print("\n=== Test 3: Double Validator Edge Cases ===")
    
    bugs_found = []
    
    # Test various edge cases
    test_cases = [
        ("inf", "infinity string"),
        ("-inf", "negative infinity string"),
        ("nan", "NaN string"),
        ("1e308", "very large number"),
        ("-1e308", "very large negative"),
        ("1e-308", "very small number"),
        ("   42   ", "number with spaces"),
        ("+42", "explicit positive"),
        ("042", "octal-like notation"),
        ("0x42", "hex notation"),
        ("1.2.3", "multiple dots"),
        ("1,234", "comma separator"),
        (True, "boolean True"),
        (False, "boolean False"),
        (None, "None value"),
    ]
    
    for value, description in test_cases:
        try:
            result = double(value)
            # Check if the result can actually be converted to float
            try:
                float_val = float(result)
                print(f"✓ {description}: {value} -> {result} -> {float_val}")
            except:
                print(f"✗ BUG: {description}: double({value}) returned {result} but can't convert to float")
                bugs_found.append((value, result))
        except (ValueError, TypeError) as e:
            print(f"✓ {description}: correctly rejected {value}")
        except Exception as e:
            print(f"✗ UNEXPECTED ERROR for {description}: {value} raised {type(e).__name__}: {e}")
            bugs_found.append((value, e))
    
    if bugs_found:
        print(f"\n✗ Found {len(bugs_found)} issues with double validator")
        return False
    return True

def test_4_resource_type_integrity():
    """Test that resource_type is correctly set"""
    print("\n=== Test 4: Resource Type Integrity ===")
    
    classes_to_test = [
        (ce.AnomalyMonitor, "AWS::CE::AnomalyMonitor"),
        (ce.AnomalySubscription, "AWS::CE::AnomalySubscription"),
        (ce.CostCategory, "AWS::CE::CostCategory"),
    ]
    
    for cls, expected_type in classes_to_test:
        if hasattr(cls, 'resource_type'):
            actual_type = cls.resource_type
            if actual_type != expected_type:
                print(f"✗ BUG: {cls.__name__}.resource_type is '{actual_type}' but should be '{expected_type}'")
                return False
            print(f"✓ {cls.__name__}.resource_type = '{actual_type}'")
        else:
            print(f"✗ BUG: {cls.__name__} missing resource_type attribute")
            return False
    
    return True

def test_5_dict_injection():
    """Test if we can inject unexpected properties"""
    print("\n=== Test 5: Dictionary Injection ===")
    
    try:
        # Try to inject unexpected property
        tag = ce.ResourceTag(Key="test", Value="test", UnexpectedProp="injected")
        result = tag.to_dict()
        
        if 'UnexpectedProp' in str(result):
            print(f"✗ BUG: Unexpected property was injected: {result}")
            return False
        
        print(f"✓ Unexpected properties are not included in output")
        return True
    except AttributeError as e:
        print(f"✓ Unexpected property correctly rejected: {e}")
        return True
    except Exception as e:
        print(f"? Unexpected error: {e}")
        return None

def test_6_type_confusion():
    """Test type confusion in properties"""
    print("\n=== Test 6: Type Confusion ===")
    
    # Test if we can pass wrong types
    try:
        # Pass a list where string is expected
        tag = ce.ResourceTag(Key=["list", "of", "strings"], Value="test")
        result = tag.to_dict()
        print(f"✗ BUG: Accepted list for Key property: {result}")
        return False
    except (TypeError, ValueError) as e:
        print(f"✓ List correctly rejected for string property")
    
    # Test if we can pass dict where string is expected
    try:
        tag = ce.ResourceTag(Key={"dict": "value"}, Value="test")
        result = tag.to_dict()
        print(f"✗ BUG: Accepted dict for Key property: {result}")
        return False
    except (TypeError, ValueError) as e:
        print(f"✓ Dict correctly rejected for string property")
    
    return True

def test_7_serialization_consistency():
    """Test JSON serialization consistency"""
    print("\n=== Test 7: Serialization Consistency ===")
    
    # Create complex object
    tags = [
        ce.ResourceTag(Key="Key1", Value="Value1"),
        ce.ResourceTag(Key="Key2", Value="Value2"),
    ]
    
    monitor = ce.AnomalyMonitor(
        MonitorName="TestMonitor",
        MonitorType="DIMENSIONAL",
        MonitorDimension="SERVICE",
        ResourceTags=tags
    )
    
    # Test to_dict
    dict1 = monitor.to_dict()
    json_str = json.dumps(dict1)
    dict2 = json.loads(json_str)
    
    if dict1 != dict2:
        print(f"✗ BUG: Serialization not consistent")
        print(f"  Original: {dict1}")
        print(f"  After JSON: {dict2}")
        return False
    
    print("✓ JSON serialization is consistent")
    return True

def test_8_none_value_handling():
    """Test how None values are handled"""
    print("\n=== Test 8: None Value Handling ===")
    
    try:
        # Try None for required field
        tag = ce.ResourceTag(Key=None, Value="test")
        result = tag.to_dict()
        
        if result.get('Key') is None:
            print(f"✗ BUG: None accepted for required Key field: {result}")
            return False
        
        print(f"Note: None was converted/handled: {result}")
        return True
    except (TypeError, ValueError) as e:
        print(f"✓ None correctly rejected for required field")
        return True

# Run all tests
def main():
    print("=" * 50)
    print("TROPOSPHERE.CE BUG HUNTING")
    print("=" * 50)
    
    tests = [
        test_1_property_override_bug,
        test_2_validation_bypass,
        test_3_double_validator_edge_cases,
        test_4_resource_type_integrity,
        test_5_dict_injection,
        test_6_type_confusion,
        test_7_serialization_consistency,
        test_8_none_value_handling,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append((test.__name__, False))
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    
    if failed > 0:
        print("\nFailed tests:")
        for name, result in results:
            if not result:
                print(f"  - {name}")

if __name__ == "__main__":
    main()