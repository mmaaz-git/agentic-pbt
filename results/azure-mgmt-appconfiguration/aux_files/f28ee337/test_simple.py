#!/usr/bin/env python3
"""
Simple test script to check for bugs in azure-mgmt-appconfiguration
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages')

import json
from azure.mgmt.appconfiguration.models import (
    ConfigurationStore,
    ApiKey,
    ApiKeyListResult,
    CheckNameAvailabilityParameters,
    Sku,
)
from azure.mgmt.appconfiguration._utils.serialization import (
    RawDeserializer,
    Model,
    full_restapi_key_transformer,
    last_restapi_key_transformer,
)

def test_model_equality_bug():
    """Test for potential bug in model equality"""
    print("Testing model equality...")
    
    # Create two identical models
    model1 = ConfigurationStore(location="eastus", sku=Sku(name="Standard"))
    model2 = ConfigurationStore(location="eastus", sku=Sku(name="Standard"))
    
    # Test equality
    if model1 == model2:
        print("✓ Models are equal as expected")
    else:
        print("✗ BUG: Identical models are not equal!")
        print(f"  model1.__dict__: {model1.__dict__}")
        print(f"  model2.__dict__: {model2.__dict__}")
        return False
    
    # Test inequality consistency
    if model1 != model2:
        print("✗ BUG: __ne__ returns True for equal models!")
        return False
    else:
        print("✓ __ne__ is consistent with __eq__")
    
    # Test with self
    if model1 == model1:
        print("✓ Reflexivity works (x == x)")
    else:
        print("✗ BUG: Model not equal to itself!")
        return False
        
    return True


def test_default_values_bug():
    """Test for bugs in default value application"""
    print("\nTesting default values...")
    
    model = ConfigurationStore(location="eastus", sku=Sku(name="Standard"))
    
    # Check defaults
    if model.disable_local_auth == False:
        print("✓ disable_local_auth default is False")
    else:
        print(f"✗ BUG: disable_local_auth default is {model.disable_local_auth}, expected False")
        return False
    
    if model.soft_delete_retention_in_days == 7:
        print("✓ soft_delete_retention_in_days default is 7")
    else:
        print(f"✗ BUG: soft_delete_retention_in_days is {model.soft_delete_retention_in_days}, expected 7")
        return False
    
    if model.enable_purge_protection == False:
        print("✓ enable_purge_protection default is False")
    else:
        print(f"✗ BUG: enable_purge_protection is {model.enable_purge_protection}, expected False")
        return False
        
    return True


def test_serialization_bug():
    """Test for bugs in serialization"""
    print("\nTesting serialization...")
    
    model = ConfigurationStore(
        location="westus",
        sku=Sku(name="Premium"),
        tags={"env": "test", "owner": "admin"},
        soft_delete_retention_in_days=30
    )
    
    try:
        serialized = model.serialize()
        
        # Check basic fields
        if serialized["location"] != "westus":
            print(f"✗ BUG: Location serialized as {serialized['location']}, expected 'westus'")
            return False
        print("✓ Location serialized correctly")
        
        if serialized["sku"]["name"] != "Premium":
            print(f"✗ BUG: SKU name serialized as {serialized['sku']['name']}, expected 'Premium'")
            return False
        print("✓ SKU serialized correctly")
        
        if serialized.get("tags") != {"env": "test", "owner": "admin"}:
            print(f"✗ BUG: Tags serialized as {serialized.get('tags')}")
            return False
        print("✓ Tags serialized correctly")
        
        if serialized["properties"]["softDeleteRetentionInDays"] != 30:
            print(f"✗ BUG: soft_delete_retention_in_days serialized incorrectly")
            return False
        print("✓ Properties serialized correctly")
        
    except Exception as e:
        print(f"✗ BUG: Serialization failed with error: {e}")
        return False
        
    return True


def test_raw_deserializer_bug():
    """Test for bugs in RawDeserializer"""
    print("\nTesting RawDeserializer...")
    
    # Test JSON deserialization
    test_data = {"key": "value", "number": 42, "nested": {"a": 1}}
    json_str = json.dumps(test_data)
    
    try:
        result = RawDeserializer.deserialize_from_text(json_str, "application/json")
        if result != test_data:
            print(f"✗ BUG: JSON deserialization failed")
            print(f"  Expected: {test_data}")
            print(f"  Got: {result}")
            return False
        print("✓ JSON deserialization works")
    except Exception as e:
        print(f"✗ BUG: JSON deserialization raised exception: {e}")
        return False
    
    # Test text deserialization
    text_data = "Hello, World!"
    result = RawDeserializer.deserialize_from_text(text_data, "text/plain")
    if result != text_data:
        print(f"✗ BUG: Text deserialization failed")
        return False
    print("✓ Text deserialization works")
    
    # Test with None content-type
    result = RawDeserializer.deserialize_from_text(text_data, None)
    if result != text_data:
        print(f"✗ BUG: Deserialization with None content-type failed")
        return False
    print("✓ None content-type handling works")
    
    return True


def test_key_transformer_bug():
    """Test for bugs in key transformers"""
    print("\nTesting key transformers...")
    
    # Test full_restapi_key_transformer with nested keys
    attr_desc = {"key": "properties.nestedKey.deepKey", "type": "str"}
    keys, value = full_restapi_key_transformer("test", attr_desc, "testvalue")
    
    expected_keys = ["properties", "nestedKey", "deepKey"]
    if keys != expected_keys:
        print(f"✗ BUG: full_restapi_key_transformer failed")
        print(f"  Expected keys: {expected_keys}")
        print(f"  Got keys: {keys}")
        return False
    print("✓ full_restapi_key_transformer works")
    
    # Test last_restapi_key_transformer
    key, value = last_restapi_key_transformer("test", attr_desc, "testvalue")
    if key != "deepKey":
        print(f"✗ BUG: last_restapi_key_transformer returned {key}, expected 'deepKey'")
        return False
    print("✓ last_restapi_key_transformer works")
    
    return True


def test_model_additional_properties():
    """Test model handling of unknown properties"""
    print("\nTesting additional properties handling...")
    
    # Try to create model with unknown property
    try:
        model = ConfigurationStore(
            location="eastus",
            sku=Sku(name="Standard"),
            unknown_property="should_be_ignored"
        )
        
        # Check that unknown property is not set
        if hasattr(model, "unknown_property"):
            print("✗ BUG: Unknown property was set as attribute")
            return False
        print("✓ Unknown properties are properly ignored")
        
        # Check that known properties still work
        if model.location != "eastus":
            print("✗ BUG: Known properties not set correctly")
            return False
            
    except Exception as e:
        print(f"✗ BUG: Model creation failed with unknown property: {e}")
        return False
        
    return True


def test_sku_equality_bug():
    """Test for potential bug in Sku model equality"""
    print("\nTesting Sku model equality...")
    
    sku1 = Sku(name="Standard")
    sku2 = Sku(name="Standard")
    sku3 = Sku(name="Premium")
    
    # Test equality of identical SKUs
    if sku1 == sku2:
        print("✓ Identical SKUs are equal")
    else:
        print("✗ BUG: Identical SKUs are not equal!")
        print(f"  sku1: {sku1.__dict__}")
        print(f"  sku2: {sku2.__dict__}")
        return False
    
    # Test inequality of different SKUs
    if sku1 != sku3:
        print("✓ Different SKUs are not equal")
    else:
        print("✗ BUG: Different SKUs are equal!")
        return False
        
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Azure App Configuration Property-Based Testing")
    print("=" * 60)
    
    all_passed = True
    
    tests = [
        test_model_equality_bug,
        test_default_values_bug,
        test_serialization_bug,
        test_raw_deserializer_bug,
        test_key_transformer_bug,
        test_model_additional_properties,
        test_sku_equality_bug,
    ]
    
    for test in tests:
        if not test():
            all_passed = False
            print(f"\n❌ Test {test.__name__} failed!")
        else:
            print(f"\n✅ Test {test.__name__} passed!")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! No bugs found.")
    else:
        print("❌ Some tests failed! Bugs were found.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())