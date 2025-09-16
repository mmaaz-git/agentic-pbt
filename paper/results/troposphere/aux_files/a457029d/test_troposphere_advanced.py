#!/usr/bin/env python3
"""Advanced property-based tests for troposphere focusing on round-trip and complex interactions."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, note
import troposphere
from troposphere import (
    Template, Parameter, Output, BaseAWSObject, AWSObject, AWSProperty,
    Tags, Tag, Ref, GetAtt, Base64, FindInMap, Join, Split, Sub,
    encode_to_dict
)


# Test round-trip properties for AWSObject serialization
class TestResource(AWSObject):
    resource_type = "AWS::Test::Resource"
    props = {
        "StringProp": (str, False),
        "IntProp": (int, False),
        "ListProp": ([str], False),
    }


@given(
    title=st.text(min_size=1, max_size=20).filter(lambda s: s.isalnum()),
    string_val=st.text(max_size=50),
    int_val=st.integers(min_value=0, max_value=1000),
    list_val=st.lists(st.text(max_size=10), max_size=5)
)
def test_awsobject_to_dict_from_dict_roundtrip(title, string_val, int_val, list_val):
    """AWSObject should survive to_dict() and from_dict() round-trip."""
    # Create object
    obj = TestResource(
        title,
        StringProp=string_val,
        IntProp=int_val,
        ListProp=list_val
    )
    
    # Convert to dict
    obj_dict = obj.to_dict(validation=False)
    
    # The Properties should be there
    assert "Type" in obj_dict
    assert obj_dict["Type"] == "AWS::Test::Resource"
    assert "Properties" in obj_dict
    
    # Create from dict
    obj2 = TestResource.from_dict(title, obj_dict["Properties"])
    
    # Compare
    assert obj2.title == obj.title
    assert obj2.properties.get("StringProp") == string_val
    assert obj2.properties.get("IntProp") == int_val
    assert obj2.properties.get("ListProp") == list_val


# Test Tags concatenation
@given(
    tags1=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(max_size=20),
        max_size=5
    ),
    tags2=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(max_size=20),
        max_size=5
    )
)
def test_tags_concatenation_associative(tags1, tags2):
    """Tags concatenation should preserve all tags."""
    t1 = Tags(tags1)
    t2 = Tags(tags2)
    
    combined = t1 + t2
    combined_dict = combined.to_dict()
    
    # All tags from t1 should be in combined
    t1_dict = t1.to_dict()
    for tag in t1_dict:
        assert tag in combined_dict
    
    # All tags from t2 should be in combined  
    t2_dict = t2.to_dict()
    for tag in t2_dict:
        assert tag in combined_dict
    
    # Combined should have all tags
    assert len(combined_dict) == len(t1_dict) + len(t2_dict)


# Test Ref equality
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda s: s.strip())
)
def test_ref_equality_reflexive(name):
    """Ref objects with same reference should be equal."""
    ref1 = Ref(name)
    ref2 = Ref(name)
    
    assert ref1 == ref2
    assert ref1 == name  # Should also equal the string directly
    assert hash(ref1) == hash(ref2)


# Test Join/Split inverse relationship
@given(
    delimiter=st.sampled_from([",", "|", "-", ":", ";"]),
    values=st.lists(
        st.text(min_size=1, max_size=10).filter(lambda s: "," not in s and "|" not in s and "-" not in s),
        min_size=1,
        max_size=5
    )
)
def test_join_split_relationship(delimiter, values):
    """Join and Split should have an inverse-like relationship in their data structure."""
    # Ensure delimiter not in values
    values = [v for v in values if delimiter not in v]
    if not values:
        values = ["test"]
    
    join_obj = Join(delimiter, values)
    split_obj = Split(delimiter, Join(delimiter, values))
    
    # Check structure
    assert "Fn::Join" in join_obj.data
    assert join_obj.data["Fn::Join"][0] == delimiter
    assert join_obj.data["Fn::Join"][1] == values
    
    assert "Fn::Split" in split_obj.data
    assert split_obj.data["Fn::Split"][0] == delimiter


# Test Template to_json/to_dict consistency
@given(
    description=st.text(max_size=100),
    num_params=st.integers(min_value=0, max_value=5),
    num_outputs=st.integers(min_value=0, max_value=5)
)
def test_template_json_dict_consistency(description, num_params, num_outputs):
    """Template's to_json() should be consistent with json.dumps(to_dict())."""
    t = Template(Description=description)
    
    # Add some parameters
    for i in range(num_params):
        param = Parameter(f"Param{i}", Type="String", Default=f"value{i}")
        t.add_parameter(param)
    
    # Add some outputs
    for i in range(num_outputs):
        output = Output(f"Output{i}", Value=f"outputvalue{i}")
        t.add_output(output)
    
    # Compare to_json with json.dumps(to_dict)
    template_json = t.to_json(indent=4, sort_keys=True)
    dict_json = json.dumps(t.to_dict(), indent=4, sort_keys=True)
    
    assert template_json == dict_json


# Test Base64 encoding property
@given(st.text(max_size=100))
def test_base64_wrapper_preserves_data(data):
    """Base64 wrapper should preserve the data in its structure."""
    b64 = Base64(data)
    
    assert "Fn::Base64" in b64.data
    assert b64.data["Fn::Base64"] == data
    
    # to_dict should preserve structure
    d = b64.to_dict()
    assert d == {"Fn::Base64": data}


# Test FindInMap with default value
@given(
    mapname=st.text(min_size=1, max_size=20),
    key1=st.text(min_size=1, max_size=20),
    key2=st.text(min_size=1, max_size=20),
    default=st.one_of(st.none(), st.text(max_size=20))
)
def test_findinmap_default_value_handling(mapname, key1, key2, default):
    """FindInMap should correctly handle optional default values."""
    fim = FindInMap(mapname, key1, key2, default)
    
    assert "Fn::FindInMap" in fim.data
    map_data = fim.data["Fn::FindInMap"]
    
    assert isinstance(map_data, list)
    assert len(map_data) >= 3
    assert map_data[0] == mapname
    assert map_data[1] == key1
    assert map_data[2] == key2
    
    if default is not None:
        assert len(map_data) == 4
        assert map_data[3] == {"DefaultValue": default}
    else:
        assert len(map_data) == 3


# Test Sub function with variable substitution
@given(
    template_str=st.text(min_size=1, max_size=50),
    variables=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(max_size=20),
        max_size=3
    )
)
def test_sub_variable_handling(template_str, variables):
    """Sub function should correctly handle variable substitutions."""
    sub = Sub(template_str, variables)
    
    assert "Fn::Sub" in sub.data
    
    if variables:
        assert isinstance(sub.data["Fn::Sub"], list)
        assert len(sub.data["Fn::Sub"]) == 2
        assert sub.data["Fn::Sub"][0] == template_str
        assert sub.data["Fn::Sub"][1] == variables
    else:
        # When no variables, should just be the string
        assert sub.data["Fn::Sub"] == template_str


# Test parameter validation for different types
@given(
    param_type=st.sampled_from(["String", "Number", "List<Number>", "CommaDelimitedList"]),
    default_value=st.one_of(
        st.text(max_size=20),
        st.integers(min_value=0, max_value=1000),
        st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
    )
)
def test_parameter_type_validation(param_type, default_value):
    """Parameters should validate default values against their types."""
    # Create parameter with specific type and default
    try:
        param = Parameter("TestParam", Type=param_type, Default=default_value)
        param.validate()
        
        # If it succeeded, verify the type matches
        if param_type == "String":
            assert isinstance(default_value, str)
        elif param_type == "Number":
            # Should be convertible to float or int
            assert isinstance(default_value, (int, float)) or (
                isinstance(default_value, str) and (
                    default_value.replace(".", "").replace("-", "").isdigit()
                )
            )
    except ValueError as e:
        # If it failed, verify it should have failed
        if param_type == "String" and not isinstance(default_value, str):
            assert "type mismatch" in str(e)
        elif param_type == "Number" and isinstance(default_value, str):
            # String should fail for Number type
            try:
                float(default_value)
                int(default_value)
                assert False, "Should have failed but didn't"
            except:
                pass  # Expected to fail


# Test equality and hashing for AWSHelperFn objects
@given(st.text(min_size=1, max_size=50))
def test_awshelperfn_equality_and_hash(value):
    """AWSHelperFn objects should have consistent equality and hashing."""
    ref1 = Ref(value)
    ref2 = Ref(value)
    ref3 = Ref(value + "different")
    
    # Same refs should be equal
    assert ref1 == ref2
    assert hash(ref1) == hash(ref2)
    
    # Different refs should not be equal
    assert ref1 != ref3
    assert hash(ref1) != hash(ref3)
    
    # Test transitivity
    base64_1 = Base64(value)
    base64_2 = Base64(value)
    
    assert base64_1 == base64_2
    assert hash(base64_1) == hash(base64_2)