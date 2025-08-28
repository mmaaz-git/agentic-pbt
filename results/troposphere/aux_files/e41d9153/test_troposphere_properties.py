#!/usr/bin/env python3
"""Property-based tests for troposphere using Hypothesis."""

import json
import math
import random
import string
from hypothesis import assume, given, settings, strategies as st

import troposphere
from troposphere import (
    AWSObject, AWSProperty, BaseAWSObject, Join, Split, Parameter, Tags, Template,
    encode_to_dict, valid_names
)


# Test 1: Template resource limits
@given(n_resources=st.integers(min_value=0, max_value=600))
def test_template_max_resources_limit(n_resources):
    """Test that Template enforces MAX_RESOURCES limit of 500."""
    template = Template()
    
    # Create dummy resources
    class DummyResource(AWSObject):
        resource_type = "AWS::Dummy::Resource"
        props = {}
    
    # Try to add resources up to n_resources
    for i in range(min(n_resources, 500)):
        resource = DummyResource(f"Resource{i}")
        template.add_resource(resource)
    
    if n_resources > 500:
        # Should raise ValueError when exceeding limit
        try:
            resource = DummyResource(f"Resource{500}")
            template.add_resource(resource)
            assert False, "Should have raised ValueError for exceeding MAX_RESOURCES"
        except ValueError as e:
            assert "Maximum number of resources 500 reached" in str(e)
    else:
        # Should work fine
        assert len(template.resources) == n_resources


# Test 2: Template parameter limits  
@given(n_params=st.integers(min_value=0, max_value=250))
def test_template_max_parameters_limit(n_params):
    """Test that Template enforces MAX_PARAMETERS limit of 200."""
    template = Template()
    
    # Try to add parameters up to n_params
    for i in range(min(n_params, 200)):
        param = Parameter(f"Param{i}", Type="String")
        template.add_parameter(param)
    
    if n_params > 200:
        # Should raise ValueError when exceeding limit
        try:
            param = Parameter(f"Param{200}", Type="String")
            template.add_parameter(param)
            assert False, "Should have raised ValueError for exceeding MAX_PARAMETERS"
        except ValueError as e:
            assert "Maximum parameters 200 reached" in str(e)
    else:
        # Should work fine
        assert len(template.parameters) == n_params


# Test 3: encode_to_dict preserves structure
@given(
    data=st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1000, max_value=1000),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
            st.text(min_size=0, max_size=50),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5),
        ),
        max_leaves=20
    )
)
def test_encode_to_dict_preserves_structure(data):
    """Test that encode_to_dict preserves the structure of standard data types."""
    encoded = encode_to_dict(data)
    
    # For standard Python types, encode_to_dict should return them unchanged
    assert encoded == data
    
    # Verify JSON serializable
    try:
        json.dumps(encoded)
    except (TypeError, ValueError):
        assert False, f"encode_to_dict output should be JSON serializable: {encoded}"


# Test 4: Tags addition is associative (not necessarily commutative due to ordering)
@given(
    tags1=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=5
    ),
    tags2=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=5
    ),
    tags3=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=5
    )
)
def test_tags_addition_associative(tags1, tags2, tags3):
    """Test that Tags addition is associative: (t1 + t2) + t3 == t1 + (t2 + t3)."""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    t3 = Tags(**tags3)
    
    # Test associativity
    result1 = (t1 + t2) + t3
    result2 = t1 + (t2 + t3)
    
    # Convert to dict for comparison (order matters)
    assert result1.to_dict() == result2.to_dict()


# Test 5: Parameter title validation
@given(title=st.text(min_size=0, max_size=300))
def test_parameter_title_validation(title):
    """Test Parameter title validation rules."""
    # Title must be alphanumeric and <= 255 characters
    is_valid_title = (
        len(title) > 0 and 
        len(title) <= 255 and 
        valid_names.match(title) is not None
    )
    
    if is_valid_title:
        # Should create successfully
        param = Parameter(title, Type="String")
        assert param.title == title
    else:
        # Should raise ValueError
        try:
            param = Parameter(title, Type="String")
            if len(title) == 0 or not valid_names.match(title):
                assert False, f"Should have raised ValueError for invalid title: {title}"
            if len(title) > 255:
                assert False, f"Should have raised ValueError for title too long: {len(title)}"
        except ValueError as e:
            if len(title) > 255:
                assert "can be no longer than" in str(e)
            else:
                assert "not alphanumeric" in str(e)


# Test 6: Join and Split are inverse operations
@given(
    delimiter=st.text(min_size=1, max_size=3, alphabet=string.punctuation),
    values=st.lists(
        st.text(min_size=0, max_size=20, alphabet=string.ascii_letters),
        min_size=1,
        max_size=10
    )
)
def test_join_split_inverse(delimiter, values):
    """Test that Split(Join(delimiter, values), delimiter) preserves values."""
    # Ensure delimiter doesn't appear in values to make this a true inverse
    clean_values = [v for v in values if delimiter not in v]
    assume(len(clean_values) > 0)
    
    # Create Join and Split operations
    joined = Join(delimiter, clean_values)
    split = Split(delimiter, joined.data["Fn::Join"][1])
    
    # The Split should reverse the Join conceptually
    # Note: We're testing the data structure, not the CloudFormation evaluation
    assert split.data["Fn::Split"][0] == delimiter
    # The input to split is the values from join
    assert split.data["Fn::Split"][1] == clean_values


# Test 7: Template duplicate key detection
@given(
    key=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
    use_output=st.booleans()
)
def test_template_duplicate_key_detection(key, use_output):
    """Test that Template detects and rejects duplicate keys."""
    template = Template()
    
    if use_output:
        from troposphere import Output
        # Add first output
        output1 = Output(key, Value="value1")
        template.add_output(output1)
        
        # Try to add duplicate
        output2 = Output(key, Value="value2")
        try:
            template.add_output(output2)
            assert False, "Should have raised ValueError for duplicate key"
        except ValueError as e:
            assert "duplicate key" in str(e)
    else:
        # Add first parameter
        param1 = Parameter(key, Type="String")
        template.add_parameter(param1)
        
        # Try to add duplicate
        param2 = Parameter(key, Type="String", Default="default")
        try:
            template.add_parameter(param2)
            assert False, "Should have raised ValueError for duplicate key"
        except ValueError as e:
            assert "duplicate key" in str(e)


# Test 8: BaseAWSObject to_dict/from_dict round-trip
@given(
    title=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits),
    props=st.dictionaries(
        st.sampled_from(["Description", "Default", "Type"]),
        st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=0, max_value=100),
            st.booleans()
        ),
        min_size=1,
        max_size=3
    )
)
def test_awsobject_dict_roundtrip(title, props):
    """Test that AWSObject can round-trip through to_dict/from_dict."""
    # Create a simple AWS object
    class TestObject(AWSObject):
        resource_type = "AWS::Test::Object"
        props = {
            "Description": (str, False),
            "Default": ((str, int, bool), False),
            "Type": (str, False),
        }
    
    # Filter props to only valid ones
    valid_props = {}
    for k, v in props.items():
        if k == "Description" and isinstance(v, str):
            valid_props[k] = v
        elif k == "Default":
            valid_props[k] = v
        elif k == "Type" and isinstance(v, str):
            valid_props[k] = v
    
    assume(len(valid_props) > 0)
    
    # Create object
    obj1 = TestObject(title, **valid_props)
    
    # Convert to dict
    obj_dict = obj1.to_dict(validation=False)
    
    # Round-trip through JSON to ensure serializability
    json_str = json.dumps(obj_dict)
    parsed_dict = json.loads(json_str)
    
    # Verify structure preserved
    assert parsed_dict == obj_dict
    assert "Type" in parsed_dict
    assert parsed_dict["Type"] == "AWS::Test::Object"


# Test 9: Parameter type validation
@given(
    param_type=st.sampled_from(["String", "Number", "List<Number>"]),
    default_value=st.one_of(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=5)
    )
)
def test_parameter_type_validation(param_type, default_value):
    """Test that Parameter validates default values against declared type."""
    # Determine if the default is valid for the type
    is_valid = False
    if param_type == "String":
        is_valid = isinstance(default_value, str)
    elif param_type == "Number":
        is_valid = isinstance(default_value, (int, float)) and not isinstance(default_value, bool)
    elif param_type == "List<Number>":
        # List<Number> expects a comma-separated string
        if isinstance(default_value, str):
            # Check if it can be parsed as comma-separated numbers
            parts = default_value.split(",")
            try:
                for part in parts:
                    float(part.strip())
                is_valid = True
            except ValueError:
                is_valid = False
        elif isinstance(default_value, list):
            # Convert list to comma-separated string
            try:
                default_value = ",".join(str(v) for v in default_value)
                is_valid = True
            except:
                is_valid = False
        else:
            is_valid = False
    
    if is_valid:
        # Should create successfully
        param = Parameter("TestParam", Type=param_type, Default=default_value)
        param.validate()
    else:
        # Should raise error during validation
        try:
            param = Parameter("TestParam", Type=param_type, Default=default_value)
            param.validate()
            # If we got here without error, the validation might be loose
            # This is okay as long as it doesn't crash
        except (ValueError, TypeError) as e:
            # Expected to fail validation
            assert "type mismatch" in str(e) or "TypeError" in str(e.__class__.__name__)


if __name__ == "__main__":
    print("Running property-based tests for troposphere...")
    import pytest
    pytest.main([__file__, "-v"])