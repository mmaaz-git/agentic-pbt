#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import json
import troposphere.forecast as forecast
from hypothesis import given, strategies as st, assume, settings

# Test more aggressive edge cases looking for bugs

# Property 1: Test calling to_dict() multiple times in sequence
def test_multiple_to_dict_calls():
    """Test that calling to_dict() multiple times doesn't cause issues"""
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Call to_dict many times
    dicts = [dataset.to_dict() for _ in range(100)]
    
    # All should be identical
    first = dicts[0]
    for d in dicts:
        assert d == first


# Property 2: Test deeply nested attributes
def test_deeply_nested_attributes():
    """Test with very deep nesting of attributes"""
    # Create a dataset with many nested attributes
    attrs = []
    for i in range(100):
        attrs.append(
            forecast.AttributesItems(
                AttributeName=f"attr_{i}_{'x' * 100}",  # Long names
                AttributeType="string"
            )
        )
    
    schema = forecast.Schema(Attributes=attrs)
    
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test" * 50,  # Long dataset name
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema,
        DataFrequency="1min",
        EncryptionConfig=forecast.EncryptionConfig(
            KmsKeyArn="arn:aws:kms:us-east-1:123456789012:key/" + "x" * 200,
            RoleArn="arn:aws:iam::123456789012:role/" + "y" * 200
        ),
        Tags=[
            forecast.TagsItems(Key="k" * 100, Value="v" * 100)
            for _ in range(50)
        ]
    )
    
    # Should be able to serialize
    dict_repr = dataset.to_dict()
    json_str = dataset.to_json()
    
    # Round trip should work
    parsed = json.loads(json_str)
    dataset2 = forecast.Dataset.from_dict("TestDataset", parsed["Properties"])
    assert dataset.to_dict() == dataset2.to_dict()


# Property 3: Test with special JSON characters
def test_json_special_characters():
    """Test handling of special JSON characters in strings"""
    special_chars = [
        '"',  # Quote
        '\\',  # Backslash
        '\n',  # Newline
        '\r',  # Carriage return
        '\t',  # Tab
        '\b',  # Backspace
        '\f',  # Form feed
        '/',  # Forward slash (sometimes escaped)
        '\u0000',  # Null character
        '\u001f',  # Unit separator
        '{"key": "value"}',  # JSON in string
        '[]',  # Array in string
        'null',  # null keyword
        'true',  # boolean keywords
        'false',
    ]
    
    for char in special_chars:
        dataset_name = f"test_{char}_dataset"
        attr_name = f"attr_{char}_name"
        
        try:
            attr = forecast.AttributesItems(
                AttributeName=attr_name,
                AttributeType="string"
            )
            
            dataset = forecast.Dataset(
                "TestDataset",
                DatasetName=dataset_name,
                DatasetType="TARGET_TIME_SERIES",
                Domain="RETAIL",
                Schema=forecast.Schema(Attributes=[attr])
            )
            
            # Should be able to serialize to JSON
            json_str = dataset.to_json()
            
            # Should be able to parse back
            parsed = json.loads(json_str)
            
            # Values should be preserved
            props = parsed["Properties"]
            assert dataset_name in str(props["DatasetName"])
            assert attr_name in str(props["Schema"]["Attributes"][0]["AttributeName"])
            
        except Exception as e:
            print(f"Failed with special char {repr(char)}: {e}")


# Property 4: Test title edge cases
def test_title_edge_cases():
    """Test edge cases for title validation"""
    # Valid edge cases
    valid_titles = [
        "A",  # Single char
        "1",  # Single digit
        "A" * 255,  # Very long
        "ABC123",  # Mixed
        "123ABC",  # Starting with number
    ]
    
    for title in valid_titles:
        dataset = forecast.Dataset(
            title,
            DatasetName="test",
            DatasetType="TARGET_TIME_SERIES",
            Domain="RETAIL",
            Schema=forecast.Schema(Attributes=[])
        )
        assert dataset.title == title
    
    # Invalid titles that should raise
    invalid_titles = [
        "",  # Empty
        "Test-Dataset",  # Hyphen
        "Test_Dataset",  # Underscore
        "Test Dataset",  # Space
        "Test.Dataset",  # Dot
        "Test@Dataset",  # Special char
        None,  # None
    ]
    
    for title in invalid_titles:
        try:
            dataset = forecast.Dataset(
                title,
                DatasetName="test",
                DatasetType="TARGET_TIME_SERIES",
                Domain="RETAIL",
                Schema=forecast.Schema(Attributes=[])
            )
            # If we get here without error, that's a potential bug
            if title is not None and title != "":
                print(f"WARNING: Invalid title '{title}' was accepted")
        except (ValueError, TypeError):
            pass  # Expected


# Property 5: Test from_dict with extra/missing keys
def test_from_dict_robustness():
    """Test from_dict with malformed input"""
    
    # Valid base properties
    valid_props = {
        "DatasetName": "test",
        "DatasetType": "TARGET_TIME_SERIES",
        "Domain": "RETAIL",
        "Schema": {"Attributes": []}
    }
    
    # Test with extra keys (should be ignored or handled gracefully)
    props_with_extra = {
        **valid_props,
        "ExtraKey": "should_be_ignored",
        "AnotherExtra": {"nested": "value"}
    }
    
    try:
        dataset = forecast.Dataset.from_dict("TestDataset", props_with_extra)
        # Extra keys should be ignored
        dict_repr = dataset.to_dict()
        assert "ExtraKey" not in dict_repr["Properties"]
        assert "AnotherExtra" not in dict_repr["Properties"]
    except AttributeError as e:
        # This is expected if extra keys cause an error
        assert "ExtraKey" in str(e) or "AnotherExtra" in str(e)


# Property 6: Test attribute mutation protection
def test_attribute_mutation():
    """Test that modifying attributes after creation works correctly"""
    attrs = [
        forecast.AttributesItems(AttributeName="attr1", AttributeType="string")
    ]
    
    schema = forecast.Schema(Attributes=attrs)
    
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    # Get initial dict
    dict1 = dataset.to_dict()
    
    # Modify the attributes list
    attrs.append(
        forecast.AttributesItems(AttributeName="attr2", AttributeType="integer")
    )
    
    # Get dict after modification
    dict2 = dataset.to_dict()
    
    # Check if modification affected the dataset
    # This tests whether the dataset stores a reference or a copy
    attrs1 = dict1["Properties"]["Schema"]["Attributes"]
    attrs2 = dict2["Properties"]["Schema"]["Attributes"]
    
    if len(attrs1) != len(attrs2):
        print(f"Mutation detected: attributes list changed from {len(attrs1)} to {len(attrs2)}")


# Property 7: Test circular references
def test_no_circular_references():
    """Ensure that objects don't create circular references"""
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Try to create a circular reference by setting properties
    # This shouldn't be possible but test it anyway
    try:
        dataset.CircularRef = dataset
        dict_repr = dataset.to_dict()
        json_str = dataset.to_json()
        # If this works, check that it doesn't cause infinite recursion
        assert len(json_str) < 100000  # Should not be huge
    except Exception:
        pass  # Expected if circular refs are prevented


# Property 8: Test concurrent access (not truly concurrent but simulated)
def test_simulated_concurrent_access():
    """Test that multiple operations on the same object work correctly"""
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Simulate "concurrent" operations
    results = []
    for i in range(100):
        if i % 3 == 0:
            results.append(dataset.to_dict())
        elif i % 3 == 1:
            results.append(dataset.to_json())
        else:
            results.append(hash(dataset))
    
    # Check consistency
    dicts = [r for r in results if isinstance(r, dict)]
    jsons = [r for r in results if isinstance(r, str)]
    hashes = [r for r in results if isinstance(r, int)]
    
    # All dicts should be identical
    if dicts:
        first_dict = dicts[0]
        for d in dicts:
            assert d == first_dict
    
    # All jsons should be identical
    if jsons:
        first_json = jsons[0]
        for j in jsons:
            assert j == first_json
    
    # All hashes should be identical
    if hashes:
        first_hash = hashes[0]
        for h in hashes:
            assert h == first_hash


# Property 9: Test property type validation
def test_property_type_validation():
    """Test that property types are validated"""
    
    # Try setting wrong types for properties
    test_cases = [
        # (property_name, wrong_value, should_fail)
        ("DatasetName", 123, True),  # Should be string
        ("DatasetName", None, False),  # None might be allowed
        ("DatasetType", ["list"], True),  # Should be string
        ("Domain", {"dict": "value"}, True),  # Should be string
        ("DataFrequency", 123, True),  # Should be string
        ("DatasetArns", "not_a_list", True),  # Should be list for DatasetGroup
    ]
    
    for prop_name, wrong_value, should_fail in test_cases:
        try:
            if prop_name == "DatasetArns":
                # Test with DatasetGroup
                group = forecast.DatasetGroup(
                    "TestGroup",
                    DatasetGroupName="test",
                    Domain="RETAIL"
                )
                setattr(group, prop_name, wrong_value)
                group.to_dict()
            else:
                # Test with Dataset
                dataset = forecast.Dataset(
                    "TestDataset",
                    DatasetName="test",
                    DatasetType="TARGET_TIME_SERIES",
                    Domain="RETAIL",
                    Schema=forecast.Schema(Attributes=[])
                )
                setattr(dataset, prop_name, wrong_value)
                dataset.to_dict()
            
            if should_fail:
                print(f"WARNING: Wrong type for {prop_name} was accepted: {wrong_value}")
        except (TypeError, AttributeError, ValueError):
            if not should_fail:
                print(f"Unexpected failure for {prop_name} with value {wrong_value}")


# Property 10: Test memory efficiency with large objects
def test_memory_efficiency():
    """Test that large objects don't cause excessive memory usage"""
    import sys
    
    # Create a large dataset
    large_dataset = forecast.Dataset(
        "LargeDataset",
        DatasetName="x" * 10000,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(
            Attributes=[
                forecast.AttributesItems(
                    AttributeName=f"attr_{i}_" + "x" * 1000,
                    AttributeType="string"
                )
                for i in range(100)
            ]
        ),
        Tags=[
            forecast.TagsItems(
                Key=f"key_{i}_" + "k" * 100,
                Value=f"value_{i}_" + "v" * 1000
            )
            for i in range(100)
        ]
    )
    
    # Get size of the object
    size = sys.getsizeof(large_dataset)
    
    # Convert to dict and JSON
    dict_repr = large_dataset.to_dict()
    json_str = large_dataset.to_json()
    
    # Sizes should be reasonable (not exponentially large)
    assert len(json_str) < 10_000_000  # Less than 10MB
    
    # Multiple calls shouldn't increase memory usage significantly
    for _ in range(10):
        _ = large_dataset.to_dict()
        _ = large_dataset.to_json()


if __name__ == "__main__":
    # Run all tests
    test_multiple_to_dict_calls()
    print("✓ test_multiple_to_dict_calls")
    
    test_deeply_nested_attributes()
    print("✓ test_deeply_nested_attributes")
    
    test_json_special_characters()
    print("✓ test_json_special_characters")
    
    test_title_edge_cases()
    print("✓ test_title_edge_cases")
    
    test_from_dict_robustness()
    print("✓ test_from_dict_robustness")
    
    test_attribute_mutation()
    print("✓ test_attribute_mutation")
    
    test_no_circular_references()
    print("✓ test_no_circular_references")
    
    test_simulated_concurrent_access()
    print("✓ test_simulated_concurrent_access")
    
    test_property_type_validation()
    print("✓ test_property_type_validation")
    
    test_memory_efficiency()
    print("✓ test_memory_efficiency")
    
    print("\nAll aggressive tests completed!")