#!/usr/bin/env python3
"""
Edge case testing for azure-mgmt-appconfiguration
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages')

import json
import datetime
from azure.mgmt.appconfiguration.models import (
    ConfigurationStore,
    ConfigurationStoreUpdateParameters,
    ApiKey,
    Sku,
    TrackedResource,
    Resource,
)
from azure.mgmt.appconfiguration._utils.serialization import (
    RawDeserializer,
    Model,
    Serializer,
    Deserializer,
    _FLATTEN,
)

def test_edge_case_empty_strings():
    """Test handling of empty strings in various fields"""
    print("Testing empty string handling...")
    
    # Test empty location (should fail as it's required)
    try:
        model = ConfigurationStore(location="", sku=Sku(name="Standard"))
        # Empty string should be accepted even though it's required
        if model.location == "":
            print("✓ Empty location string accepted")
        else:
            print(f"✗ BUG: Location became {model.location}")
            return False
    except Exception as e:
        print(f"✗ Empty location raised exception: {e}")
        return False
        
    # Test empty SKU name
    try:
        sku = Sku(name="")
        if sku.name == "":
            print("✓ Empty SKU name accepted")
        else:
            print(f"✗ BUG: SKU name became {sku.name}")
            return False
    except Exception as e:
        print(f"✗ Empty SKU name raised exception: {e}")
        return False
        
    return True


def test_edge_case_none_values():
    """Test handling of None values in optional fields"""
    print("\nTesting None value handling...")
    
    # Test with explicit None values
    model = ConfigurationStore(
        location="eastus",
        sku=Sku(name="Standard"),
        tags=None,
        identity=None,
        encryption=None,
    )
    
    # Check None values are preserved
    if model.tags is None:
        print("✓ None tags preserved")
    else:
        print(f"✗ BUG: Tags became {model.tags} instead of None")
        return False
        
    # Check serialization with None values
    serialized = model.serialize()
    
    # None values might be omitted or included as null
    print(f"  Serialized tags: {serialized.get('tags', 'NOT PRESENT')}")
    
    return True


def test_edge_case_boundary_values():
    """Test boundary values for integer fields"""
    print("\nTesting boundary values...")
    
    # Test minimum retention days
    model1 = ConfigurationStore(
        location="eastus",
        sku=Sku(name="Standard"),
        soft_delete_retention_in_days=0
    )
    if model1.soft_delete_retention_in_days == 0:
        print("✓ Zero retention days accepted")
    else:
        print(f"✗ BUG: Retention days became {model1.soft_delete_retention_in_days}")
        return False
    
    # Test negative retention days (should be accepted but might be invalid)
    model2 = ConfigurationStore(
        location="eastus",
        sku=Sku(name="Standard"),
        soft_delete_retention_in_days=-1
    )
    if model2.soft_delete_retention_in_days == -1:
        print("✓ Negative retention days accepted (no validation)")
    else:
        print(f"✗ BUG: Negative retention days became {model2.soft_delete_retention_in_days}")
        return False
    
    # Test very large retention days
    model3 = ConfigurationStore(
        location="eastus",
        sku=Sku(name="Standard"),
        soft_delete_retention_in_days=999999999
    )
    if model3.soft_delete_retention_in_days == 999999999:
        print("✓ Large retention days accepted")
    else:
        print(f"✗ BUG: Large retention days became {model3.soft_delete_retention_in_days}")
        return False
        
    return True


def test_edge_case_special_characters():
    """Test handling of special characters in strings"""
    print("\nTesting special character handling...")
    
    special_chars = "!@#$%^&*(){}[]|\\:;\"'<>,.?/~`"
    unicode_chars = "你好世界🌍émojis™"
    
    # Test special characters in tags
    model = ConfigurationStore(
        location="eastus",
        sku=Sku(name="Standard"),
        tags={
            special_chars: "value1",
            "key2": unicode_chars,
            "": "empty_key",  # Empty key
        }
    )
    
    if model.tags[special_chars] == "value1":
        print("✓ Special characters in tag keys preserved")
    else:
        print("✗ BUG: Special characters in tags not preserved")
        return False
        
    if model.tags["key2"] == unicode_chars:
        print("✓ Unicode characters in tag values preserved")
    else:
        print("✗ BUG: Unicode characters not preserved")
        return False
        
    if model.tags[""] == "empty_key":
        print("✓ Empty string as tag key accepted")
    else:
        print("✗ BUG: Empty tag key not preserved")
        return False
        
    # Test serialization
    serialized = model.serialize()
    if serialized["tags"][special_chars] == "value1":
        print("✓ Special characters survive serialization")
    else:
        print("✗ BUG: Special characters lost in serialization")
        return False
        
    return True


def test_edge_case_json_injection():
    """Test for JSON injection vulnerabilities"""
    print("\nTesting JSON injection handling...")
    
    # Try injecting JSON structure in string fields
    injection_attempt = '", "injected": "value", "original": "'
    
    model = ConfigurationStore(
        location=injection_attempt,
        sku=Sku(name="Standard")
    )
    
    serialized = model.serialize()
    
    # Check if injection was properly escaped
    if serialized["location"] == injection_attempt:
        print("✓ JSON injection attempt properly handled")
    else:
        print(f"✗ Potential issue with JSON injection")
        print(f"  Input: {injection_attempt}")
        print(f"  Output: {serialized['location']}")
        return False
        
    # Verify the serialized JSON is valid
    try:
        json_str = json.dumps(serialized)
        parsed = json.loads(json_str)
        if parsed["location"] == injection_attempt:
            print("✓ Serialized JSON remains valid")
        else:
            print("✗ BUG: JSON parsing changed the value")
            return False
    except Exception as e:
        print(f"✗ BUG: JSON serialization/parsing failed: {e}")
        return False
        
    return True


def test_edge_case_deserializer_malformed():
    """Test RawDeserializer with malformed inputs"""
    print("\nTesting malformed input handling...")
    
    # Test malformed JSON
    malformed_json = '{"key": "value", "broken": '
    try:
        result = RawDeserializer.deserialize_from_text(malformed_json, "application/json")
        print(f"✗ BUG: Malformed JSON didn't raise error, returned: {result}")
        return False
    except Exception:
        print("✓ Malformed JSON properly raises exception")
    
    # Test empty string
    try:
        result = RawDeserializer.deserialize_from_text("", "application/json")
        # Empty string might be valid (null/None)
        print(f"  Empty JSON string returns: {result}")
    except Exception as e:
        print(f"  Empty JSON string raises: {e}")
    
    # Test with BOM character
    bom_json = '\ufeff{"key": "value"}'
    try:
        result = RawDeserializer.deserialize_from_text(bom_json, "application/json")
        if result == {"key": "value"}:
            print("✓ BOM character properly handled")
        else:
            print(f"✗ BUG: BOM handling issue, got: {result}")
            return False
    except Exception as e:
        print(f"✗ BUG: BOM character caused exception: {e}")
        return False
        
    return True


def test_edge_case_model_comparison():
    """Test model comparison edge cases"""
    print("\nTesting model comparison edge cases...")
    
    # Test comparison with different types
    model = ConfigurationStore(location="eastus", sku=Sku(name="Standard"))
    
    # Compare with None
    if model == None:
        print("✗ BUG: Model equals None!")
        return False
    else:
        print("✓ Model not equal to None")
    
    # Compare with dict
    if model == {"location": "eastus"}:
        print("✗ BUG: Model equals dict!")
        return False
    else:
        print("✓ Model not equal to dict")
    
    # Compare with string
    if model == "ConfigurationStore":
        print("✗ BUG: Model equals string!")
        return False
    else:
        print("✓ Model not equal to string")
    
    # Test != with non-model types
    if model != None:
        print("✓ Model != None works")
    else:
        print("✗ BUG: Model != None returns False")
        return False
        
    return True


def test_edge_case_update_parameters():
    """Test ConfigurationStoreUpdateParameters edge cases"""
    print("\nTesting update parameters edge cases...")
    
    # Create update with all None values
    update = ConfigurationStoreUpdateParameters()
    
    # Check all fields are None by default
    if update.tags is None and update.sku is None:
        print("✓ All optional fields default to None")
    else:
        print("✗ BUG: Some fields have non-None defaults")
        return False
    
    # Serialize empty update
    serialized = update.serialize()
    
    # Check serialization of empty object
    print(f"  Empty update serialized to: {serialized}")
    
    # Test with some fields set
    update2 = ConfigurationStoreUpdateParameters(
        tags={},  # Empty dict
        disable_local_auth=True,
        enable_purge_protection=None,  # Explicit None
    )
    
    serialized2 = update2.serialize()
    
    if serialized2.get("tags") == {}:
        print("✓ Empty dict preserved in serialization")
    else:
        print(f"✗ BUG: Empty dict became {serialized2.get('tags')}")
        return False
        
    return True


def test_flatten_regex():
    """Test the _FLATTEN regex used for key parsing"""
    print("\nTesting _FLATTEN regex...")
    
    # Test normal case
    result = _FLATTEN.split("properties.nestedKey")
    if result == ["properties", "nestedKey"]:
        print("✓ Normal nested key split correctly")
    else:
        print(f"✗ BUG: Normal split failed: {result}")
        return False
    
    # Test escaped dot
    result = _FLATTEN.split(r"properties\.escaped.key")
    expected = [r"properties\.escaped", "key"]
    if result == expected:
        print("✓ Escaped dot handled correctly")
    else:
        print(f"✗ Escaped dot handling issue: {result}")
        print(f"  Expected: {expected}")
        # This might not be a bug if escaping isn't supported
    
    # Test multiple dots
    result = _FLATTEN.split("a.b.c.d.e")
    if result == ["a", "b", "c", "d", "e"]:
        print("✓ Multiple dots split correctly")
    else:
        print(f"✗ BUG: Multiple dots failed: {result}")
        return False
        
    return True


def test_readonly_field_behavior():
    """Test behavior of readonly fields"""
    print("\nTesting readonly field behavior...")
    
    # ApiKey has all readonly fields
    key = ApiKey()
    
    # Try to set readonly field after creation
    original_id = key.id
    try:
        key.id = "new_id"
        if key.id == "new_id":
            print("⚠ Readonly field 'id' can be modified after creation")
        else:
            print("✓ Readonly field not modified")
    except Exception as e:
        print(f"✓ Setting readonly field raised: {e}")
    
    # Check if readonly fields are None by default
    if key.id is None and key.name is None and key.value is None:
        print("✓ Readonly fields default to None")
    else:
        print("✗ BUG: Readonly fields have non-None defaults")
        return False
        
    return True


def main():
    """Run all edge case tests"""
    print("=" * 60)
    print("Azure App Configuration Edge Case Testing")
    print("=" * 60)
    
    all_passed = True
    
    tests = [
        test_edge_case_empty_strings,
        test_edge_case_none_values,
        test_edge_case_boundary_values,
        test_edge_case_special_characters,
        test_edge_case_json_injection,
        test_edge_case_deserializer_malformed,
        test_edge_case_model_comparison,
        test_edge_case_update_parameters,
        test_flatten_regex,
        test_readonly_field_behavior,
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
                print(f"\n❌ Test {test.__name__} failed!")
            else:
                print(f"\n✅ Test {test.__name__} passed!")
        except Exception as e:
            all_passed = False
            print(f"\n❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All edge case tests passed!")
    else:
        print("❌ Some edge case tests failed!")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())