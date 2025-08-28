"""Test edge cases with Tags in troposphere.iotfleethub.Application"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, settings
import troposphere.iotfleethub as iotfleethub
from troposphere import Tags


# Test with various tag keys and values
@given(
    tag_key=st.text(),
    tag_value=st.text()
)
def test_arbitrary_tag_keys_values(tag_key, tag_value):
    """Test that any string can be used as tag key/value"""
    
    try:
        app = iotfleethub.Application(
            "TestApp",
            ApplicationName="MyApp",
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            Tags=Tags({tag_key: tag_value})
        )
        
        d = app.to_dict()
        
        # Check the tags are preserved
        if "Tags" in d["Properties"]:
            tags_list = d["Properties"]["Tags"]
            # Tags should be a list of dicts with Key and Value
            assert isinstance(tags_list, list)
            if len(tags_list) > 0:
                tag_dict = tags_list[0]
                assert tag_dict["Key"] == tag_key
                assert tag_dict["Value"] == tag_value
        
        # Try JSON serialization
        json_str = app.to_json()
        parsed = json.loads(json_str)
        
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        # Some strings might cause issues
        pass


@given(
    num_duplicates=st.integers(min_value=2, max_value=10)
)
def test_duplicate_tag_keys(num_duplicates):
    """Test behavior with duplicate tag keys"""
    
    # Create tags with duplicate keys but different values
    tags_dict = {}
    key = "DuplicateKey"
    
    for i in range(num_duplicates):
        tags_dict[key] = f"Value{i}"  # This will overwrite previous values
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=Tags(tags_dict)
    )
    
    d = app.to_dict()
    
    if "Tags" in d["Properties"]:
        tags_list = d["Properties"]["Tags"]
        # Should only have one tag since dict keys are unique
        assert len(tags_list) == 1
        assert tags_list[0]["Key"] == key
        # Should have the last value
        assert tags_list[0]["Value"] == f"Value{num_duplicates - 1}"


@given(
    empty_key=st.just(""),
    value=st.text()
)
def test_empty_string_tag_key(empty_key, value):
    """Test tags with empty string as key"""
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=Tags({empty_key: value})
    )
    
    d = app.to_dict()
    
    if "Tags" in d["Properties"]:
        tags_list = d["Properties"]["Tags"]
        assert len(tags_list) == 1
        assert tags_list[0]["Key"] == ""
        assert tags_list[0]["Value"] == value


def test_tags_with_multiple_dict_args():
    """Test Tags with multiple dict arguments"""
    
    tags = Tags(
        {"Key1": "Value1"},
        {"Key2": "Value2"},
        {"Key3": "Value3"}
    )
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=tags
    )
    
    d = app.to_dict()
    
    if "Tags" in d["Properties"]:
        tags_list = d["Properties"]["Tags"]
        assert len(tags_list) == 3
        
        # Check all tags are present
        tag_dict = {tag["Key"]: tag["Value"] for tag in tags_list}
        assert tag_dict == {"Key1": "Value1", "Key2": "Value2", "Key3": "Value3"}


def test_tags_with_mixed_args():
    """Test Tags with mixed arguments (kwargs and dict)"""
    
    # Try mixing different ways of specifying tags
    tags1 = Tags(Key1="Value1", Key2="Value2")
    tags2 = Tags({"Key3": "Value3", "Key4": "Value4"})
    
    app1 = iotfleethub.Application(
        "TestApp1",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=tags1
    )
    
    app2 = iotfleethub.Application(
        "TestApp2",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=tags2
    )
    
    d1 = app1.to_dict()
    d2 = app2.to_dict()
    
    print(f"Tags from kwargs: {d1.get('Properties', {}).get('Tags')}")
    print(f"Tags from dict: {d2.get('Properties', {}).get('Tags')}")


@given(
    keys=st.lists(st.text(min_size=1), min_size=5, max_size=5, unique=True)
)
def test_tags_ordering(keys):
    """Test if tag ordering is preserved"""
    
    # Create tags dict with specific order
    tags_dict = {key: f"Value_{key}" for key in keys}
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=Tags(tags_dict)
    )
    
    d = app.to_dict()
    
    if "Tags" in d["Properties"]:
        tags_list = d["Properties"]["Tags"]
        returned_keys = [tag["Key"] for tag in tags_list]
        
        # Check if all keys are present (order might not be preserved)
        assert set(returned_keys) == set(keys)