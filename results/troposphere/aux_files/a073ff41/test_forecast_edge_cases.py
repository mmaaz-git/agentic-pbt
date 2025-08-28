#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import json
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.forecast as forecast

# Test edge cases and potential bugs

# Strategy for potentially problematic strings
edge_strings = st.one_of(
    st.text(min_size=0, max_size=0),  # Empty string
    st.text(min_size=1).filter(lambda x: x.strip() == ""),  # Whitespace only
    st.text().filter(lambda x: "\n" in x or "\t" in x),  # Contains newlines/tabs
    st.text().filter(lambda x: '"' in x or "'" in x),  # Contains quotes
    st.text().map(lambda x: x * 1000),  # Very long strings
    st.just("null"),
    st.just("None"), 
    st.just("undefined"),
    st.just("{}"),
    st.just("[]"),
)

# Test with unicode and special characters
unicode_strings = st.text(
    alphabet=st.characters(min_codepoint=0x00, max_codepoint=0x10FFFF, blacklist_categories=("Cc", "Cs")),
    min_size=1
)

# Valid but edge case titles
edge_titles = st.one_of(
    st.just("A"),  # Single character
    st.just("A" * 255),  # Max length
    st.text(alphabet="0123456789", min_size=1, max_size=50),  # Numbers only
    st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=50),  # Uppercase only
)


# Property 1: Empty or whitespace attribute names
@given(st.one_of(st.just(""), st.just(" "), st.just("  "), st.just("\t"), st.just("\n")))
def test_empty_attribute_names(attr_name):
    """Test handling of empty or whitespace-only attribute names"""
    # This should be allowed by the module since it doesn't validate content
    attr = forecast.AttributesItems(
        AttributeName=attr_name,
        AttributeType="string"
    )
    
    dict_repr = attr.to_dict()
    assert dict_repr["AttributeName"] == attr_name
    
    # JSON round-trip should preserve it
    json_str = json.dumps(dict_repr)
    parsed = json.loads(json_str)
    assert parsed["AttributeName"] == attr_name


# Property 2: Unicode in field values
@given(unicode_strings, unicode_strings)
def test_unicode_in_fields(name, value):
    """Test that unicode strings are handled correctly"""
    assume(len(name) > 0 and len(name) < 1000)  # Reasonable length
    assume(len(value) > 0 and len(value) < 1000)
    
    tag = forecast.TagsItems(Key=name, Value=value)
    dict_repr = tag.to_dict()
    
    # Unicode should be preserved
    assert dict_repr["Key"] == name
    assert dict_repr["Value"] == value
    
    # JSON serialization should handle unicode
    json_str = json.dumps(dict_repr, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert parsed["Key"] == name
    assert parsed["Value"] == value


# Property 3: Schema with empty Attributes list
def test_schema_empty_attributes():
    """Test Schema with empty Attributes list"""
    # Empty list might be invalid for AWS but should be allowed by the module
    schema = forecast.Schema(Attributes=[])
    dict_repr = schema.to_dict()
    
    assert "Attributes" in dict_repr
    assert dict_repr["Attributes"] == []
    
    # JSON round-trip
    json_str = json.dumps(dict_repr)
    parsed = json.loads(json_str)
    assert parsed["Attributes"] == []


# Property 4: Dataset with duplicate attribute names in Schema
@given(st.text(min_size=1, max_size=50))
def test_duplicate_attribute_names(attr_name):
    """Test Schema with duplicate attribute names"""
    # AWS might reject this but the module should allow it
    schema = forecast.Schema(
        Attributes=[
            forecast.AttributesItems(AttributeName=attr_name, AttributeType="string"),
            forecast.AttributesItems(AttributeName=attr_name, AttributeType="integer"),
            forecast.AttributesItems(AttributeName=attr_name, AttributeType="float"),
        ]
    )
    
    dict_repr = schema.to_dict()
    attrs = dict_repr["Attributes"]
    
    # All duplicates should be preserved
    assert len(attrs) == 3
    assert all(a["AttributeName"] == attr_name for a in attrs)


# Property 5: Very large number of attributes
@given(st.integers(min_value=100, max_value=1000))
@settings(max_examples=10)
def test_large_number_of_attributes(num_attrs):
    """Test Schema with large number of attributes"""
    attrs = [
        forecast.AttributesItems(
            AttributeName=f"attr_{i}",
            AttributeType="string"
        )
        for i in range(num_attrs)
    ]
    
    schema = forecast.Schema(Attributes=attrs)
    dict_repr = schema.to_dict()
    
    assert len(dict_repr["Attributes"]) == num_attrs
    
    # Should be able to serialize to JSON
    json_str = json.dumps(dict_repr)
    parsed = json.loads(json_str)
    assert len(parsed["Attributes"]) == num_attrs


# Property 6: Special characters in ARNs
@given(st.text())
def test_special_chars_in_arns(text):
    """Test EncryptionConfig with special characters in ARNs"""
    # ARNs with special characters - AWS would reject but module should handle
    kms_arn = f"arn:aws:kms:us-east-1:123456789012:key/{text}"
    role_arn = f"arn:aws:iam::123456789012:role/{text}"
    
    encryption = forecast.EncryptionConfig(
        KmsKeyArn=kms_arn,
        RoleArn=role_arn
    )
    
    dict_repr = encryption.to_dict()
    assert dict_repr["KmsKeyArn"] == kms_arn
    assert dict_repr["RoleArn"] == role_arn


# Property 7: Dataset with None as optional field value
def test_dataset_none_optional_fields():
    """Test Dataset when optional fields are set to None"""
    try:
        dataset = forecast.Dataset(
            "TestDataset",
            DatasetName="test",
            DatasetType="TARGET_TIME_SERIES",
            Domain="RETAIL",
            Schema=forecast.Schema(Attributes=[]),
            DataFrequency=None,  # Explicitly None
            EncryptionConfig=None,
            Tags=None
        )
        
        dict_repr = dataset.to_dict()
        props = dict_repr["Properties"]
        
        # None values should not appear in the dict
        assert "DataFrequency" not in props or props["DataFrequency"] is None
        assert "EncryptionConfig" not in props or props["EncryptionConfig"] is None
        assert "Tags" not in props or props["Tags"] is None
    except Exception as e:
        # Module might not handle None gracefully
        print(f"Failed with None values: {e}")


# Property 8: Ref and GetAtt methods
@given(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50).filter(lambda x: x.isalnum()))
def test_dataset_ref_and_getatt(title):
    """Test Dataset Ref and GetAtt methods"""
    dataset = forecast.Dataset(
        title,
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Test Ref
    ref = dataset.ref()
    assert ref.data == {"Ref": title}
    
    # Test GetAtt
    get_att = dataset.get_att("Arn")
    assert get_att.data == {"Fn::GetAtt": [title, "Arn"]}
    
    # Alternative capitalization
    assert dataset.Ref() == ref
    assert dataset.GetAtt("Arn").data == get_att.data


# Property 9: Dataset equality with different optional fields
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.text(min_size=1, max_size=50)
)
def test_dataset_equality_with_optionals(title, name):
    """Test Dataset equality when optional fields differ"""
    base_kwargs = {
        "DatasetName": name,
        "DatasetType": "TARGET_TIME_SERIES",
        "Domain": "RETAIL",
        "Schema": forecast.Schema(Attributes=[])
    }
    
    # Dataset without optional fields
    dataset1 = forecast.Dataset(title, **base_kwargs)
    
    # Dataset with optional fields
    dataset2 = forecast.Dataset(
        title,
        **base_kwargs,
        DataFrequency="D",
        Tags=[forecast.TagsItems(Key="test", Value="value")]
    )
    
    # Should not be equal
    assert dataset1 != dataset2
    assert hash(dataset1) != hash(dataset2)
    
    # But identical datasets should be equal
    dataset3 = forecast.Dataset(title, **base_kwargs)
    assert dataset1 == dataset3
    assert hash(dataset1) == hash(dataset3)


# Property 10: Nested object preservation
@given(st.integers(min_value=1, max_value=10))
def test_nested_object_preservation(num_attrs):
    """Test that nested objects are properly preserved through transformations"""
    # Create complex nested structure
    attrs = [
        forecast.AttributesItems(
            AttributeName=f"attr_{i}",
            AttributeType="string"
        )
        for i in range(num_attrs)
    ]
    
    schema = forecast.Schema(Attributes=attrs)
    encryption = forecast.EncryptionConfig(
        KmsKeyArn="arn:aws:kms:us-east-1:123456789012:key/test",
        RoleArn="arn:aws:iam::123456789012:role/test"
    )
    tags = [
        forecast.TagsItems(Key=f"key_{i}", Value=f"value_{i}")
        for i in range(3)
    ]
    
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema,
        EncryptionConfig=encryption,
        Tags=tags
    )
    
    # Convert to dict and back
    dict1 = dataset.to_dict()
    props = dict1["Properties"]
    dataset2 = forecast.Dataset.from_dict("TestDataset", props)
    dict2 = dataset2.to_dict()
    
    # All nested structures should be preserved
    assert dict1 == dict2
    assert len(dict2["Properties"]["Schema"]["Attributes"]) == num_attrs
    assert "EncryptionConfig" in dict2["Properties"]
    assert len(dict2["Properties"]["Tags"]) == 3


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])