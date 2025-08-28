#!/usr/bin/env python3
"""Analyze potential bugs in troposphere.iotcoredeviceadvisor by running specific test cases"""

import sys
import json

# Add the environment path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotcoredeviceadvisor as iotcore
from troposphere.validators import boolean

def test_boolean_edge_cases():
    """Test boolean validator with various edge case inputs"""
    print("\n=== Testing Boolean Validator ===")
    
    test_cases = [
        # Valid cases
        (True, True, "True boolean"),
        (False, False, "False boolean"),
        (1, True, "Integer 1"),
        (0, False, "Integer 0"),
        ("true", True, "String 'true'"),
        ("false", False, "String 'false'"),
        ("True", True, "String 'True'"),
        ("False", False, "String 'False'"),
        ("1", True, "String '1'"),
        ("0", False, "String '0'"),
        
        # Edge cases that might fail
        ("TRUE", None, "All caps TRUE"),
        ("FALSE", None, "All caps FALSE"),
        ("yes", None, "String 'yes'"),
        ("no", None, "String 'no'"),
        (1.0, None, "Float 1.0"),
        (0.0, None, "Float 0.0"),
        (2, None, "Integer 2"),
        (-1, None, "Integer -1"),
        ("", None, "Empty string"),
        (None, None, "None value"),
    ]
    
    bugs_found = []
    
    for input_val, expected, description in test_cases:
        try:
            result = boolean(input_val)
            if expected is None:
                # This should have raised an error
                bugs_found.append(f"boolean({repr(input_val)}) returned {result} but should have raised ValueError")
                print(f"  BUG: {description} - Accepted invalid input {repr(input_val)} -> {result}")
            elif result != expected:
                bugs_found.append(f"boolean({repr(input_val)}) returned {result} but expected {expected}")
                print(f"  BUG: {description} - Wrong result for {repr(input_val)}")
            else:
                print(f"  OK: {description} - {repr(input_val)} -> {result}")
        except (ValueError, TypeError) as e:
            if expected is not None:
                bugs_found.append(f"boolean({repr(input_val)}) raised {type(e).__name__} but expected {expected}")
                print(f"  BUG: {description} - Rejected valid input {repr(input_val)}")
            else:
                print(f"  OK: {description} - Correctly rejected {repr(input_val)}")
    
    return bugs_found


def test_required_field_validation():
    """Test that required fields are properly validated"""
    print("\n=== Testing Required Field Validation ===")
    
    bugs_found = []
    
    # Test 1: Missing required DevicePermissionRoleArn
    print("  Test: Missing DevicePermissionRoleArn (required)")
    try:
        config = iotcore.SuiteDefinitionConfiguration(
            RootGroup="TestGroup"
            # Missing DevicePermissionRoleArn
        )
        result = config.to_dict()  # Validation happens here
        bugs_found.append("SuiteDefinitionConfiguration accepted missing required field DevicePermissionRoleArn")
        print(f"    BUG: Missing required field was accepted")
    except ValueError as e:
        if "required" in str(e).lower():
            print(f"    OK: Correctly rejected missing required field")
        else:
            print(f"    WARNING: Rejected but with unexpected message: {e}")
    
    # Test 2: Missing required RootGroup
    print("  Test: Missing RootGroup (required)")
    try:
        config = iotcore.SuiteDefinitionConfiguration(
            DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole"
            # Missing RootGroup
        )
        result = config.to_dict()
        bugs_found.append("SuiteDefinitionConfiguration accepted missing required field RootGroup")
        print(f"    BUG: Missing required field was accepted")
    except ValueError as e:
        if "required" in str(e).lower():
            print(f"    OK: Correctly rejected missing required field")
        else:
            print(f"    WARNING: Rejected but with unexpected message: {e}")
    
    # Test 3: Both required fields present
    print("  Test: Both required fields present")
    try:
        config = iotcore.SuiteDefinitionConfiguration(
            DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
            RootGroup="TestGroup"
        )
        result = config.to_dict()
        print(f"    OK: Accepted valid configuration")
    except Exception as e:
        bugs_found.append(f"SuiteDefinitionConfiguration rejected valid configuration: {e}")
        print(f"    BUG: Rejected valid configuration: {e}")
    
    return bugs_found


def test_title_validation():
    """Test title validation for resources"""
    print("\n=== Testing Title Validation ===")
    
    bugs_found = []
    
    # Create a valid config for testing
    config = iotcore.SuiteDefinitionConfiguration(
        DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
        RootGroup="TestGroup"
    )
    
    test_cases = [
        ("ValidTitle123", True, "Alphanumeric title"),
        ("", False, "Empty title"),
        ("test-name", False, "Title with hyphen"),
        ("test_name", False, "Title with underscore"),
        ("test.name", False, "Title with dot"),
        ("test name", False, "Title with space"),
        ("123!@#", False, "Title with special chars"),
        (None, True, "None title (optional)"),  # Title is optional
    ]
    
    for title, should_succeed, description in test_cases:
        try:
            suite = iotcore.SuiteDefinition(
                title=title,
                SuiteDefinitionConfiguration=config
            )
            if should_succeed:
                print(f"  OK: {description} - Accepted {repr(title)}")
            else:
                bugs_found.append(f"SuiteDefinition accepted invalid title: {repr(title)}")
                print(f"  BUG: {description} - Accepted invalid title {repr(title)}")
        except ValueError as e:
            if should_succeed:
                bugs_found.append(f"SuiteDefinition rejected valid title: {repr(title)}")
                print(f"  BUG: {description} - Rejected valid title {repr(title)}")
            else:
                if "alphanumeric" in str(e).lower():
                    print(f"  OK: {description} - Correctly rejected {repr(title)}")
                else:
                    print(f"  WARNING: {description} - Rejected with unexpected message: {e}")
    
    return bugs_found


def test_type_validation():
    """Test type validation for fields"""
    print("\n=== Testing Type Validation ===")
    
    bugs_found = []
    
    # Test invalid types for Devices field (should be list)
    invalid_devices = [
        ("string", "String instead of list"),
        (123, "Integer instead of list"),
        ({"key": "value"}, "Dict instead of list"),
        (["string1", "string2"], "List of strings instead of DeviceUnderTest"),
    ]
    
    for invalid_value, description in invalid_devices:
        print(f"  Test: {description}")
        try:
            config = iotcore.SuiteDefinitionConfiguration(
                DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
                RootGroup="TestGroup",
                Devices=invalid_value
            )
            # Try to serialize
            result = config.to_dict()
            bugs_found.append(f"SuiteDefinitionConfiguration accepted invalid Devices type: {type(invalid_value)}")
            print(f"    BUG: Accepted invalid type {type(invalid_value).__name__}")
        except (TypeError, AttributeError, ValueError) as e:
            print(f"    OK: Correctly rejected invalid type")
    
    # Test valid Devices field
    print(f"  Test: Valid list of DeviceUnderTest")
    try:
        device = iotcore.DeviceUnderTest(
            CertificateArn="arn:aws:iot:us-east-1:123456789012:cert/abc",
            ThingArn="arn:aws:iot:us-east-1:123456789012:thing/MyThing"
        )
        config = iotcore.SuiteDefinitionConfiguration(
            DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
            RootGroup="TestGroup",
            Devices=[device]
        )
        result = config.to_dict()
        print(f"    OK: Accepted valid Devices list")
    except Exception as e:
        bugs_found.append(f"SuiteDefinitionConfiguration rejected valid Devices: {e}")
        print(f"    BUG: Rejected valid Devices: {e}")
    
    return bugs_found


def test_serialization_consistency():
    """Test serialization consistency and round-trip properties"""
    print("\n=== Testing Serialization Consistency ===")
    
    bugs_found = []
    
    # Create a complex nested structure
    device1 = iotcore.DeviceUnderTest(
        CertificateArn="arn:aws:iot:us-east-1:123456789012:cert/abc",
        ThingArn="arn:aws:iot:us-east-1:123456789012:thing/Thing1"
    )
    device2 = iotcore.DeviceUnderTest(
        CertificateArn="arn:aws:iot:us-east-1:123456789012:cert/def"
        # No ThingArn - testing optional field
    )
    
    config = iotcore.SuiteDefinitionConfiguration(
        DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
        RootGroup="TestGroup",
        Devices=[device1, device2],
        IntendedForQualification=True,
        SuiteDefinitionName="TestSuite"
    )
    
    suite = iotcore.SuiteDefinition(
        title="MySuiteDefinition",
        SuiteDefinitionConfiguration=config
    )
    
    # Test 1: Serialize to dict
    print("  Test: Serialization to dict")
    try:
        suite_dict = suite.to_dict()
        
        # Check expected structure
        assert 'Type' in suite_dict, "Missing 'Type' field"
        assert suite_dict['Type'] == 'AWS::IoTCoreDeviceAdvisor::SuiteDefinition', f"Wrong Type: {suite_dict['Type']}"
        assert 'Properties' in suite_dict, "Missing 'Properties' field"
        
        props = suite_dict['Properties']
        assert 'SuiteDefinitionConfiguration' in props, "Missing SuiteDefinitionConfiguration"
        
        config_dict = props['SuiteDefinitionConfiguration']
        assert config_dict['DevicePermissionRoleArn'] == "arn:aws:iam::123456789012:role/TestRole"
        assert config_dict['RootGroup'] == "TestGroup"
        assert len(config_dict['Devices']) == 2
        assert config_dict['IntendedForQualification'] == True
        assert config_dict['SuiteDefinitionName'] == "TestSuite"
        
        print("    OK: Serialization produces expected structure")
    except Exception as e:
        bugs_found.append(f"Serialization failed: {e}")
        print(f"    BUG: {e}")
    
    # Test 2: JSON serialization round-trip
    print("  Test: JSON serialization round-trip")
    try:
        json_str = json.dumps(suite_dict)
        parsed = json.loads(json_str)
        
        if parsed != suite_dict:
            bugs_found.append("JSON round-trip changed the data structure")
            print(f"    BUG: JSON round-trip modified data")
        else:
            print("    OK: JSON round-trip preserves data")
    except Exception as e:
        bugs_found.append(f"JSON serialization failed: {e}")
        print(f"    BUG: {e}")
    
    return bugs_found


def main():
    """Run all bug hunting tests"""
    print("="*70)
    print("PROPERTY-BASED BUG HUNTING FOR troposphere.iotcoredeviceadvisor")
    print("="*70)
    
    all_bugs = []
    
    # Run each test category
    all_bugs.extend(test_boolean_edge_cases())
    all_bugs.extend(test_required_field_validation())
    all_bugs.extend(test_title_validation())
    all_bugs.extend(test_type_validation())
    all_bugs.extend(test_serialization_consistency())
    
    # Print summary
    print("\n" + "="*70)
    print("BUG HUNTING SUMMARY")
    print("="*70)
    
    if all_bugs:
        print(f"\nFound {len(all_bugs)} potential bug(s):\n")
        for i, bug in enumerate(all_bugs, 1):
            print(f"{i}. {bug}")
    else:
        print("\nNo bugs found! All tests passed successfully.")
    
    print("\n" + "="*70)
    
    return len(all_bugs)


if __name__ == "__main__":
    sys.exit(main())