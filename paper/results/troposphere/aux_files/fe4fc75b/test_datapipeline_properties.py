#!/usr/bin/env python3
"""Property-based testing for troposphere.datapipeline module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import datapipeline, validators
from troposphere import BaseAWSObject
import json


# Test Property 1: Boolean validator accepts only specific values
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_accepts_correct_values(value):
    """Test that boolean validator accepts only documented values."""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        assert validators.boolean(value) is True
    elif value in valid_false:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test Property 2: Required fields must be present during validation
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=1),
    include_required=st.booleans()
)
def test_required_fields_validation(name, include_required):
    """Test that required fields are enforced during validation."""
    pipeline = datapipeline.Pipeline(name)
    
    if include_required:
        pipeline.Name = "TestPipeline"
    
    try:
        pipeline.to_dict()
        # Should succeed only if required field is included
        assert include_required
    except ValueError as e:
        # Should fail only if required field is missing
        assert not include_required
        assert "required in type" in str(e)


# Test Property 3: Title validation - must be alphanumeric
@given(st.text())
def test_title_validation_alphanumeric(title):
    """Test that titles must be alphanumeric only."""
    try:
        pipeline = datapipeline.Pipeline(title)
        # Title should only succeed if alphanumeric
        assert title and title.isalnum()
    except ValueError as e:
        # Should fail if not alphanumeric
        assert "not alphanumeric" in str(e)
        assert not (title and title.isalnum())


# Test Property 4: Type validation in properties
@given(
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_pipeline_name_type_validation(value):
    """Test that Pipeline.Name only accepts strings."""
    pipeline = datapipeline.Pipeline("ValidTitle123")
    
    if isinstance(value, str):
        pipeline.Name = value
        assert pipeline.Name == value
    else:
        with pytest.raises(TypeError) as exc:
            pipeline.Name = value
        assert "expected" in str(exc.value)


# Test Property 5: ObjectField mutual exclusivity
@given(
    key=st.text(min_size=1),
    ref_value=st.text(min_size=1),
    string_value=st.text(min_size=1),
    use_both=st.booleans()
)
def test_object_field_values(key, ref_value, string_value, use_both):
    """Test ObjectField can have RefValue OR StringValue but not necessarily both."""
    if use_both:
        # Should allow both (they're both optional)
        field = datapipeline.ObjectField(
            Key=key,
            RefValue=ref_value,
            StringValue=string_value
        )
        assert field.Key == key
        assert field.RefValue == ref_value
        assert field.StringValue == string_value
    else:
        # Should allow either one
        field1 = datapipeline.ObjectField(Key=key, RefValue=ref_value)
        assert field1.Key == key
        assert field1.RefValue == ref_value
        
        field2 = datapipeline.ObjectField(Key=key, StringValue=string_value)
        assert field2.Key == key
        assert field2.StringValue == string_value


# Test Property 6: to_dict serialization for valid objects
@given(
    id_val=st.text(min_size=1),
    string_val=st.text()
)
def test_parameter_value_to_dict(id_val, string_val):
    """Test that ParameterValue serializes correctly to dict."""
    param = datapipeline.ParameterValue(
        Id=id_val,
        StringValue=string_val
    )
    
    result = param.to_dict()
    assert isinstance(result, dict)
    assert result.get("Id") == id_val
    assert result.get("StringValue") == string_val


# Test Property 7: List properties accept lists
@given(
    st.lists(
        st.builds(
            lambda k, v: datapipeline.ParameterObjectAttribute(Key=k, StringValue=v),
            st.text(min_size=1),
            st.text()
        ),
        min_size=1
    )
)
def test_parameter_object_attributes_list(attributes):
    """Test that ParameterObject.Attributes accepts a list of ParameterObjectAttribute."""
    param_obj = datapipeline.ParameterObject(
        Id="test_id",
        Attributes=attributes
    )
    
    assert param_obj.Attributes == attributes
    assert len(param_obj.Attributes) == len(attributes)
    
    # Verify serialization works
    result = param_obj.to_dict()
    assert "Attributes" in result
    assert len(result["Attributes"]) == len(attributes)


# Test Property 8: Pipeline accepts boolean for Activate field
@given(
    activate_value=st.one_of(
        st.sampled_from([True, False, 0, 1, "true", "false", "True", "False"]),
        st.text(),
        st.integers(),
        st.floats()
    )
)
def test_pipeline_activate_boolean_property(activate_value):
    """Test that Pipeline.Activate uses boolean validator."""
    pipeline = datapipeline.Pipeline("TestPipeline123")
    pipeline.Name = "MyPipeline"
    
    valid_values = [True, False, 0, 1, "0", "1", "true", "false", "True", "False"]
    
    if activate_value in valid_values:
        pipeline.Activate = activate_value
        # The value should be converted to boolean
        assert pipeline.Activate in [True, False]
    else:
        with pytest.raises((TypeError, ValueError)):
            pipeline.Activate = activate_value


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing troposphere.datapipeline properties...")
    test_boolean_validator_accepts_correct_values()
    print("✓ Boolean validator test passed")