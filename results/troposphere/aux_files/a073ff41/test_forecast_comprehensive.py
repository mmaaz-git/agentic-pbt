#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import json
import copy
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.forecast as forecast

# Test more comprehensive properties and potential edge cases

# Valid alphanumeric titles strategy
valid_titles = st.text(
    alphabet=st.characters(min_codepoint=48, max_codepoint=122).filter(lambda c: c.isalnum()),
    min_size=1,
    max_size=50
)

# Property 1: Test that modifying the original object doesn't affect to_dict output
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_to_dict_immutability(title, dataset_name):
    """Test that to_dict returns a new dict that isn't affected by later modifications"""
    dataset = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(
            Attributes=[
                forecast.AttributesItems(AttributeName="test", AttributeType="string")
            ]
        )
    )
    
    # Get first dict
    dict1 = dataset.to_dict()
    dict1_copy = copy.deepcopy(dict1)
    
    # Modify the dataset
    dataset.DatasetName = "modified_name"
    dataset.Domain = "CUSTOM"
    
    # Get second dict
    dict2 = dataset.to_dict()
    
    # dict1 should not have been affected
    assert dict1 == dict1_copy, "Original dict was modified"
    
    # dict2 should reflect the changes
    assert dict2["Properties"]["DatasetName"] == "modified_name"
    assert dict2["Properties"]["Domain"] == "CUSTOM"


# Property 2: Test comparison with dict
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_dataset_dict_comparison(title, dataset_name):
    """Test that Dataset can be compared with its dict representation"""
    dataset = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    dict_repr = dataset.to_dict()
    
    # Dataset should equal its dict representation plus title
    expected_dict = {"title": title, **dict_repr}
    assert dataset == expected_dict


# Property 3: Test hash consistency across equivalent objects
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_hash_consistency(title, dataset_name):
    """Test that equivalent objects have the same hash even if created differently"""
    # Create dataset directly
    dataset1 = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Create dataset from dict
    dict_repr = dataset1.to_dict()
    dataset2 = forecast.Dataset.from_dict(title, dict_repr["Properties"])
    
    # Create dataset with same values but different object instances
    dataset3 = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # All should have the same hash
    h1, h2, h3 = hash(dataset1), hash(dataset2), hash(dataset3)
    assert h1 == h2 == h3, f"Hashes differ: {h1}, {h2}, {h3}"


# Property 4: Test JSON with indent and sort_keys parameters
@given(
    valid_titles,
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=10),
    st.booleans()
)
def test_json_parameters(title, dataset_name, indent, sort_keys):
    """Test that to_json respects indent and sort_keys parameters"""
    dataset = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(
            Attributes=[
                forecast.AttributesItems(AttributeName="b_attr", AttributeType="string"),
                forecast.AttributesItems(AttributeName="a_attr", AttributeType="integer"),
            ]
        )
    )
    
    json_str = dataset.to_json(indent=indent, sort_keys=sort_keys)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # If sort_keys is True, keys should be sorted in the JSON string
    if sort_keys:
        # Keys should appear in alphabetical order in the string
        props_start = json_str.find('"Properties"')
        type_start = json_str.find('"Type"')
        assert props_start < type_start, "Keys not sorted in JSON output"


# Property 5: Test that validation is optional
@given(valid_titles)
def test_validation_optional(title):
    """Test that validation can be disabled"""
    # Create dataset without required fields
    dataset = forecast.Dataset(title)
    
    # With validation disabled, to_dict should not raise
    dict_repr = dataset.to_dict(validation=False)
    assert isinstance(dict_repr, dict)
    
    # to_json with validation=False should also work
    json_str = dataset.to_json(validation=False)
    assert json.loads(json_str) is not None
    
    # But with validation enabled, it should fail
    try:
        dataset.to_dict(validation=True)
        assert False, "Validation should have failed"
    except ValueError:
        pass  # Expected


# Property 6: Test no_validation() method
@given(valid_titles)
def test_no_validation_method(title):
    """Test the no_validation() method"""
    # Create dataset without required fields
    dataset = forecast.Dataset(title).no_validation()
    
    # Should be able to convert to dict without error
    dict_repr = dataset.to_dict()
    assert isinstance(dict_repr, dict)
    
    # do_validation should be False
    assert dataset.do_validation == False


# Property 7: Test with AWS helper functions (Ref, GetAtt, etc.)
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_with_aws_helper_functions(title, dataset_name):
    """Test that AWS helper functions work with Dataset"""
    from troposphere import Ref, GetAtt, Sub
    
    # Create dataset with references
    dataset = forecast.Dataset(
        title,
        DatasetName=Ref("DatasetNameParameter"),
        DatasetType="TARGET_TIME_SERIES",
        Domain=Sub("${DomainParam}"),
        Schema=forecast.Schema(Attributes=[])
    )
    
    dict_repr = dataset.to_dict()
    props = dict_repr["Properties"]
    
    # References should be preserved as dicts
    assert isinstance(props["DatasetName"], dict)
    assert "Ref" in props["DatasetName"]
    assert isinstance(props["Domain"], dict)
    assert "Fn::Sub" in props["Domain"]


# Property 8: Test that resource_type is correctly set
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_resource_type(title, dataset_name):
    """Test that resource_type is correctly set"""
    dataset = forecast.Dataset(
        title,
        DatasetName=dataset_name,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    assert dataset.resource_type == "AWS::Forecast::Dataset"
    
    dict_repr = dataset.to_dict()
    assert dict_repr["Type"] == "AWS::Forecast::Dataset"
    
    # DatasetGroup should have different resource_type
    group = forecast.DatasetGroup(
        title,
        DatasetGroupName="test",
        Domain="RETAIL"
    )
    
    assert group.resource_type == "AWS::Forecast::DatasetGroup"
    assert group.to_dict()["Type"] == "AWS::Forecast::DatasetGroup"


# Property 9: Test Tags class usage
@given(valid_titles, st.text(min_size=1, max_size=50))
def test_tags_class_usage(title, dataset_name):
    """Test using the base Tags class with DatasetGroup"""
    from troposphere import Tags
    
    # DatasetGroup uses the base Tags class, not TagsItems
    tags = Tags(
        Environment="Production",
        Owner="DataTeam",
        Project="Forecasting"
    )
    
    group = forecast.DatasetGroup(
        title,
        DatasetGroupName=dataset_name,
        Domain="RETAIL",
        Tags=tags
    )
    
    dict_repr = group.to_dict()
    props = dict_repr["Properties"]
    
    # Tags should be present and properly formatted
    assert "Tags" in props
    assert isinstance(props["Tags"], list)
    assert len(props["Tags"]) == 3
    
    # Check that tags are sorted (Tags class sorts by key)
    tag_keys = [tag["Key"] for tag in props["Tags"]]
    assert tag_keys == sorted(tag_keys)


# Property 10: Test mutation after creation
@given(valid_titles, st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50))
def test_mutation_after_creation(title, name1, name2):
    """Test that objects can be mutated after creation"""
    assume(name1 != name2)
    
    dataset = forecast.Dataset(
        title,
        DatasetName=name1,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    # Get initial state
    dict1 = dataset.to_dict()
    assert dict1["Properties"]["DatasetName"] == name1
    
    # Mutate the dataset
    dataset.DatasetName = name2
    
    # Get new state
    dict2 = dataset.to_dict()
    assert dict2["Properties"]["DatasetName"] == name2
    assert dict1 != dict2
    
    # Mutation should affect equality
    dataset2 = forecast.Dataset(
        title,
        DatasetName=name1,
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=forecast.Schema(Attributes=[])
    )
    
    assert dataset != dataset2  # Different names
    
    # Update dataset2 to match
    dataset2.DatasetName = name2
    assert dataset == dataset2  # Now they match


# Property 11: Test required field validation message
@given(valid_titles)
def test_required_field_validation_message(title):
    """Test that validation error messages are informative"""
    dataset = forecast.Dataset(title, DatasetName="test")
    
    try:
        dataset.to_dict()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        # Should mention the missing field
        assert "DatasetType" in error_msg or "Domain" in error_msg or "Schema" in error_msg
        # Should mention the resource type
        assert "AWS::Forecast::Dataset" in error_msg
        # Should mention the title
        assert title in error_msg


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])