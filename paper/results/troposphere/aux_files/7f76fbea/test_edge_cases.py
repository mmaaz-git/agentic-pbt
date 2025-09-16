#!/usr/bin/env python3
"""Test for potential edge cases and bugs in troposphere.iottwinmaker."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere
from troposphere import iottwinmaker
from troposphere.validators.iottwinmaker import validate_listvalue, validate_nestedtypel
import json
import traceback


def test_recursive_datavalue_bug():
    """Test for potential infinite recursion with nested DataValues."""
    print("\nTesting recursive DataValue structures...")
    
    # Create nested DataValue in ListValue
    inner_dv1 = iottwinmaker.DataValue(StringValue="inner1")
    inner_dv2 = iottwinmaker.DataValue(IntegerValue=42)
    
    try:
        # This should work according to the validator
        outer_dv = iottwinmaker.DataValue(ListValue=[inner_dv1, inner_dv2])
        outer_dict = outer_dv.to_dict()
        
        # Check if nested structure is preserved
        assert "ListValue" in outer_dict
        assert len(outer_dict["ListValue"]) == 2
        print("✓ Nested DataValue in ListValue works correctly")
        
        # Try even deeper nesting
        nested_list_dv = iottwinmaker.DataValue(ListValue=[outer_dv])
        nested_dict = nested_list_dv.to_dict()
        print("✓ Double-nested DataValue works")
        
    except Exception as e:
        print(f"✗ Found issue with nested DataValue: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_datatype_recursive_bug():
    """Test for potential infinite recursion with NestedType."""
    print("\nTesting recursive DataType structures...")
    
    try:
        # Create a DataType with NestedType
        inner_dt = iottwinmaker.DataType(Type="STRING")
        outer_dt = iottwinmaker.DataType(NestedType=inner_dt)
        
        outer_dict = outer_dt.to_dict()
        assert "NestedType" in outer_dict
        assert outer_dict["NestedType"]["Type"] == "STRING"
        print("✓ Nested DataType works correctly")
        
        # Try deeper nesting
        deeper_dt = iottwinmaker.DataType(NestedType=outer_dt)
        deeper_dict = deeper_dt.to_dict()
        print("✓ Double-nested DataType works")
        
    except Exception as e:
        print(f"✗ Found issue with nested DataType: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_mapvalue_edge_cases():
    """Test MapValue field of DataValue with various dict inputs."""
    print("\nTesting MapValue edge cases...")
    
    # Test with empty dict
    dv1 = iottwinmaker.DataValue(MapValue={})
    assert dv1.to_dict()["MapValue"] == {}
    print("✓ Empty MapValue dict works")
    
    # Test with nested dicts
    complex_map = {
        "key1": {"nested": "value"},
        "key2": [1, 2, 3],
        "key3": None
    }
    dv2 = iottwinmaker.DataValue(MapValue=complex_map)
    assert dv2.to_dict()["MapValue"] == complex_map
    print("✓ Complex MapValue dict works")
    
    return True


def test_json_serialization_edge_cases():
    """Test JSON serialization with special characters and edge cases."""
    print("\nTesting JSON serialization edge cases...")
    
    # Test with unicode and special characters
    special_strings = [
        "Hello 🦄 World",  # Unicode emoji
        "Tab\there",  # Tab character
        "New\nline",  # Newline
        "Quote\"test",  # Quote
        "Backslash\\test",  # Backslash
        "",  # Empty string
        " " * 100,  # Many spaces
    ]
    
    for special_str in special_strings:
        try:
            dv = iottwinmaker.DataValue(StringValue=special_str)
            dv_dict = dv.to_dict()
            
            # Try to serialize to JSON and back
            json_str = json.dumps(dv_dict)
            parsed = json.loads(json_str)
            
            assert parsed["StringValue"] == special_str, f"Failed for: {repr(special_str)}"
            
        except Exception as e:
            print(f"✗ JSON serialization failed for {repr(special_str)}: {e}")
            return False
    
    print("✓ JSON serialization handles special characters correctly")
    return True


def test_property_definitions_dict_bug():
    """Test PropertyDefinitions as dict property in ComponentType."""
    print("\nTesting PropertyDefinitions dict handling...")
    
    try:
        # Create PropertyDefinition objects
        prop_def1 = iottwinmaker.PropertyDefinition(
            IsTimeSeries=True,
            DataType=iottwinmaker.DataType(Type="DOUBLE")
        )
        
        prop_def2 = iottwinmaker.PropertyDefinition(
            IsRequiredInEntity=True,
            DataType=iottwinmaker.DataType(Type="STRING")
        )
        
        # Create ComponentType with PropertyDefinitions dict
        ct = iottwinmaker.ComponentType(
            "TestComponentType",
            ComponentTypeId="comp-123",
            WorkspaceId="workspace-123",
            PropertyDefinitions={
                "temperature": prop_def1,
                "status": prop_def2
            }
        )
        
        ct_dict = ct.to_dict(validation=False)
        props = ct_dict["Properties"]["PropertyDefinitions"]
        
        assert "temperature" in props
        assert "status" in props
        assert props["temperature"]["IsTimeSeries"] == True
        assert props["status"]["IsRequiredInEntity"] == True
        
        print("✓ PropertyDefinitions dict handling works correctly")
        
    except Exception as e:
        print(f"✗ Found issue with PropertyDefinitions dict: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_tags_dict_edge_cases():
    """Test Tags dict property with various inputs."""
    print("\nTesting Tags dict edge cases...")
    
    # Test with various tag values
    tags_tests = [
        {},  # Empty tags
        {"Key": "Value"},  # Simple tag
        {"Key1": "", "Key2": ""},  # Empty values
        {"🦄": "emoji"},  # Emoji key
        {"a" * 100: "b" * 100},  # Long keys and values
    ]
    
    for tags in tags_tests:
        try:
            entity = iottwinmaker.Entity(
                "TestEntity",
                EntityName="test",
                WorkspaceId="workspace-123",
                Tags=tags
            )
            
            entity_dict = entity.to_dict(validation=False)
            if tags:  # Only check if tags were provided
                assert entity_dict["Properties"]["Tags"] == tags
                
        except Exception as e:
            print(f"✗ Tags dict failed for {tags}: {e}")
            return False
    
    print("✓ Tags dict handles various inputs correctly")
    return True


def test_from_dict_round_trip():
    """Test from_dict and to_dict round-trip consistency."""
    print("\nTesting from_dict/to_dict round-trip...")
    
    try:
        # Create a complex Entity
        original = iottwinmaker.Entity(
            "TestEntity",
            EntityName="MyEntity",
            WorkspaceId="workspace-123",
            Description="Test description",
            ParentEntityId="parent-123",
            Tags={"env": "test", "version": "1.0"}
        )
        
        # Convert to dict
        original_dict = original.to_dict(validation=False)
        
        # Create new entity from dict
        recreated = iottwinmaker.Entity.from_dict(
            "TestEntity",
            original_dict["Properties"]
        )
        
        # Convert back to dict
        recreated_dict = recreated.to_dict(validation=False)
        
        # They should be equal
        assert original_dict == recreated_dict, "Round-trip failed"
        print("✓ from_dict/to_dict round-trip works correctly")
        
    except Exception as e:
        print(f"✗ Round-trip test failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_component_properties_dict():
    """Test Component with Properties dict field."""
    print("\nTesting Component Properties dict...")
    
    try:
        # Create Property objects
        prop1 = iottwinmaker.Property(
            Value=iottwinmaker.DataValue(StringValue="test")
        )
        
        prop2 = iottwinmaker.Property(
            Definition=iottwinmaker.Definition(
                IsTimeSeries=True,
                DataType=iottwinmaker.DataType(Type="DOUBLE")
            )
        )
        
        # Create Component with Properties dict
        component = iottwinmaker.Component(
            ComponentName="TestComponent",
            ComponentTypeId="comp-type-123",
            Properties={
                "prop1": prop1,
                "prop2": prop2
            }
        )
        
        comp_dict = component.to_dict(validation=False)
        props = comp_dict["Properties"]
        
        assert "prop1" in props
        assert "prop2" in props
        
        print("✓ Component Properties dict works correctly")
        
    except Exception as e:
        print(f"✗ Component Properties dict failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_allowed_values_in_datatype():
    """Test DataType with AllowedValues list."""
    print("\nTesting DataType AllowedValues...")
    
    try:
        # Create DataValues for allowed values
        allowed1 = iottwinmaker.DataValue(StringValue="ACTIVE")
        allowed2 = iottwinmaker.DataValue(StringValue="INACTIVE")
        allowed3 = iottwinmaker.DataValue(StringValue="ERROR")
        
        # Create DataType with AllowedValues
        dt = iottwinmaker.DataType(
            Type="STRING",
            AllowedValues=[allowed1, allowed2, allowed3]
        )
        
        dt_dict = dt.to_dict()
        
        assert "AllowedValues" in dt_dict
        assert len(dt_dict["AllowedValues"]) == 3
        assert dt_dict["AllowedValues"][0]["StringValue"] == "ACTIVE"
        
        print("✓ DataType AllowedValues works correctly")
        
    except Exception as e:
        print(f"✗ DataType AllowedValues failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_scene_metadata_dict():
    """Test Scene with SceneMetadata dict."""
    print("\nTesting Scene SceneMetadata dict...")
    
    try:
        complex_metadata = {
            "version": "1.0",
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "empty": {}
        }
        
        scene = iottwinmaker.Scene(
            "TestScene",
            SceneId="scene-123",
            ContentLocation="s3://bucket/scene",
            WorkspaceId="workspace-123",
            SceneMetadata=complex_metadata
        )
        
        scene_dict = scene.to_dict(validation=False)
        
        assert scene_dict["Properties"]["SceneMetadata"] == complex_metadata
        print("✓ Scene SceneMetadata dict works correctly")
        
    except Exception as e:
        print(f"✗ Scene SceneMetadata dict failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all edge case tests."""
    print("=" * 60)
    print("Testing Edge Cases and Potential Bugs")
    print("=" * 60)
    
    all_passed = True
    
    tests = [
        test_recursive_datavalue_bug,
        test_datatype_recursive_bug,
        test_mapvalue_edge_cases,
        test_json_serialization_edge_cases,
        test_property_definitions_dict_bug,
        test_tags_dict_edge_cases,
        test_from_dict_round_trip,
        test_component_properties_dict,
        test_allowed_values_in_datatype,
        test_scene_metadata_dict,
    ]
    
    for test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"✗ {test_func.__name__} crashed: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All edge case tests passed!")
    else:
        print("❌ Some tests failed or found bugs!")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())