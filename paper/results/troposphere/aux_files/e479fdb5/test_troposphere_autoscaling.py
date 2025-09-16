#!/usr/bin/env python3
"""Property-based tests for troposphere.autoscaling module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from hypothesis import settings
import pytest

from troposphere.validators import boolean, integer, double
from troposphere.validators.autoscaling import validate_int_to_str, Tags
from troposphere.autoscaling import AutoScalingGroup, LaunchTemplateSpecification
from troposphere import AWSProperty


# Test 1: Boolean validator accepts specific values
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator(value):
    """Test that boolean validator correctly handles all input types"""
    
    # These should return True
    if value in [True, 1, "1", "true", "True"]:
        assert boolean(value) is True
    # These should return False  
    elif value in [False, 0, "0", "false", "False"]:
        assert boolean(value) is False
    # Everything else should raise ValueError
    else:
        with pytest.raises(ValueError):
            boolean(value)


# Test 2: Integer validator with edge cases
@given(st.one_of(
    st.integers(),
    st.text(min_size=1),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator(value):
    """Test integer validator handles various input types correctly"""
    
    try:
        # Try to convert to int
        int(value)
        # If successful, integer() should return the original value
        result = integer(value)
        assert result == value
    except (ValueError, TypeError):
        # If int() fails, integer() should also raise ValueError
        with pytest.raises(ValueError):
            integer(value)


# Test 3: Double validator
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(min_size=1),
    st.none(),
    st.lists(st.floats()),
    st.dictionaries(st.text(), st.floats())
))
def test_double_validator(value):
    """Test double validator handles various input types correctly"""
    
    try:
        # Try to convert to float
        float(value)
        # If successful, double() should return the original value
        result = double(value)
        assert result == value
    except (ValueError, TypeError):
        # If float() fails, double() should also raise ValueError
        with pytest.raises(ValueError):
            double(value)


# Test 4: validate_int_to_str backward compatibility
@given(st.one_of(
    st.integers(),
    st.text(min_size=1),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_validate_int_to_str(value):
    """Test backward compatibility function for int/str conversion"""
    
    if isinstance(value, int):
        # Integers should be converted to string
        result = validate_int_to_str(value)
        assert result == str(value)
        assert isinstance(result, str)
    elif isinstance(value, str):
        try:
            # If string can be converted to int, it should return string of that int
            int_val = int(value)
            result = validate_int_to_str(value)
            assert result == str(int_val)
            assert isinstance(result, str)
        except (ValueError, TypeError):
            # If string can't be converted to int, should raise TypeError
            with pytest.raises(TypeError):
                validate_int_to_str(value)
    else:
        # All other types should raise TypeError
        with pytest.raises(TypeError):
            validate_int_to_str(value)


# Test 5: Tags class behavior
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.text(),
            st.tuples(st.text(), st.booleans()),
            st.tuples(st.text(), st.sampled_from([0, 1, "true", "false", True, False]))
        ),
        min_size=0,
        max_size=10
    )
)
def test_tags_class(tags_dict):
    """Test Tags class initialization and conversion"""
    
    # Create Tags object
    tags = Tags(**tags_dict)
    
    # Convert to dict
    result = tags.to_dict()
    
    # Should be a list
    assert isinstance(result, list)
    
    # Should have same number of items as input dict
    assert len(result) == len(tags_dict)
    
    # Each item should have required keys
    for tag in result:
        assert "Key" in tag
        assert "Value" in tag
        assert "PropagateAtLaunch" in tag
        assert isinstance(tag["PropagateAtLaunch"], bool)


# Test 6: Property validation with None values  
@given(st.one_of(
    st.none(),
    st.text(min_size=1),
    st.integers()
))
def test_property_none_handling(value):
    """Test how properties handle None values"""
    
    class TestProperty(AWSProperty):
        props = {
            "TestField": (str, False),  # Optional string field
        }
    
    if value is None:
        # None values should be acceptable for optional fields
        prop = TestProperty(TestField=value)
        # The property should be set
        assert hasattr(prop, 'properties')
        assert 'TestField' in prop.properties
        assert prop.properties['TestField'] is None
    elif isinstance(value, str):
        prop = TestProperty(TestField=value)
        assert prop.properties['TestField'] == value
    else:
        # Non-string values (except None) should fail type check
        with pytest.raises(TypeError):
            TestProperty(TestField=value)


# Test 7: LaunchTemplateSpecification validation
@given(
    st.one_of(
        st.builds(dict, LaunchTemplateId=st.text(min_size=1), Version=st.text()),
        st.builds(dict, LaunchTemplateName=st.text(min_size=1), Version=st.text()),
        st.builds(dict, LaunchTemplateId=st.text(), LaunchTemplateName=st.text(), Version=st.text()),
        st.builds(dict, Version=st.text())
    )
)
def test_launch_template_specification(kwargs):
    """Test LaunchTemplateSpecification validation rules"""
    
    has_id = "LaunchTemplateId" in kwargs
    has_name = "LaunchTemplateName" in kwargs
    has_version = "Version" in kwargs
    
    if has_version and (has_id or has_name) and not (has_id and has_name):
        # Should succeed when exactly one of ID or Name is provided with Version
        spec = LaunchTemplateSpecification(**kwargs)
        spec.validate()
    elif has_version and has_id and has_name:
        # Should fail when both ID and Name are provided
        spec = LaunchTemplateSpecification(**kwargs)
        with pytest.raises(ValueError):
            spec.validate()
    elif has_version and not has_id and not has_name:
        # Should fail when neither ID nor Name is provided
        with pytest.raises(ValueError):
            LaunchTemplateSpecification(**kwargs)