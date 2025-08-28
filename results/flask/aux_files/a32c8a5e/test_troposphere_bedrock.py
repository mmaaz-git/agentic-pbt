#!/usr/bin/env python3
"""Property-based tests for troposphere.bedrock module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import math
from troposphere.validators import boolean, integer, double
from troposphere import bedrock
from troposphere import BaseAWSObject, AWSObject


# Test 1: Boolean validator input/output contract
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles documented valid inputs"""
    result = boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.none(),
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(allow_nan=False),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Integer validator accepts valid integers
@given(st.integers())
def test_integer_validator_with_integers(value):
    """Test that integer validator accepts actual integers"""
    result = integer(value)
    assert result == value
    # Should be convertible to int
    assert int(result) == value


@given(st.text(min_size=1).filter(lambda x: x.strip().lstrip('-').isdigit()))
def test_integer_validator_with_string_integers(value):
    """Test that integer validator accepts string representations of integers"""
    result = integer(value)
    assert result == value
    # Should be convertible to int
    int(result)  # Should not raise


@given(st.one_of(
    st.floats(allow_nan=False).filter(lambda x: not x.is_integer()),
    st.text().filter(lambda x: not (x.strip().lstrip('-').isdigit() if x.strip() else False)),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_invalid_inputs(value):
    """Test that integer validator raises ValueError for non-integer inputs"""
    assume(value is not None or True)  # None should raise
    with pytest.raises(ValueError):
        integer(value)


# Test 3: Double validator accepts valid floats
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_with_floats(value):
    """Test that double validator accepts floats"""
    result = double(value)
    assert result == value
    # Should be convertible to float
    assert float(result) == value


@given(st.integers())
def test_double_validator_with_integers(value):
    """Test that double validator accepts integers (as they're valid floats)"""
    result = double(value)
    assert result == value
    # Should be convertible to float
    assert float(result) == value


@given(st.text(min_size=1).map(str.strip).filter(
    lambda x: x and all(c in '0123456789.-+eE' for c in x)
).filter(lambda x: x.count('.') <= 1 and x.count('e') <= 1 and x.count('E') <= 1))
def test_double_validator_with_numeric_strings(value):
    """Test that double validator accepts string representations of numbers"""
    # Only test strings that Python can convert to float
    try:
        float(value)
        is_valid = True
    except ValueError:
        is_valid = False
    
    if is_valid:
        result = double(value)
        assert result == value


@given(st.one_of(
    st.text().filter(lambda x: not all(c in '0123456789.-+eE ' for c in x.strip())),
    st.none(),
    st.lists(st.floats())
))
def test_double_validator_invalid_inputs(value):
    """Test that double validator raises ValueError for non-numeric inputs"""
    # Check if it's actually invalid
    try:
        if value is not None:
            float(value)
        else:
            raise ValueError
        # If we get here, it's actually valid, skip this test case
        assume(False)
    except (ValueError, TypeError):
        # This is expected to be invalid
        with pytest.raises(ValueError):
            double(value)


# Test 4: AWS Object type validation and required fields
def test_aws_object_required_fields():
    """Test that AWS objects enforce required fields"""
    # AgentAliasRoutingConfigurationListItem has AgentVersion as required
    obj = bedrock.AgentAliasRoutingConfigurationListItem()
    
    # Should have no AgentVersion initially
    with pytest.raises(AttributeError):
        _ = obj.AgentVersion
    
    # Setting it should work
    obj.AgentVersion = "1.0"
    assert obj.AgentVersion == "1.0"


@given(st.text())
def test_aws_object_string_property(value):
    """Test that string properties accept strings"""
    obj = bedrock.AgentAliasRoutingConfigurationListItem()
    obj.AgentVersion = value
    assert obj.AgentVersion == value


@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_aws_object_type_validation(value):
    """Test that AWS objects validate property types"""
    obj = bedrock.S3Identifier()
    
    # S3BucketName expects a string
    if isinstance(value, str):
        obj.S3BucketName = value
        assert obj.S3BucketName == value
    else:
        with pytest.raises(TypeError):
            obj.S3BucketName = value


# Test 5: Title validation for alphanumeric names
@given(st.text(alphabet=st.characters(categories=['Lu', 'Ll', 'Nd']), min_size=1))
def test_valid_alphanumeric_titles(title):
    """Test that alphanumeric titles are accepted"""
    # Agent requires AgentName which is different from title
    try:
        obj = bedrock.Agent(title=title, AgentName="TestAgent")
        assert obj.title == title
    except ValueError:
        # Title validation failed, this should only happen for non-alphanumeric
        assert not title.replace('_', '').isalnum()


@given(st.text().filter(lambda x: x and not x.isalnum()))
def test_invalid_titles_with_special_chars(title):
    """Test that non-alphanumeric titles are rejected"""
    assume(any(not c.isalnum() for c in title))
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        bedrock.Agent(title=title, AgentName="TestAgent")


@given(st.sampled_from(["", None]))
def test_empty_or_none_titles(title):
    """Test that empty or None titles are rejected"""
    with pytest.raises(ValueError):
        bedrock.Agent(title=title, AgentName="TestAgent")


# Test 6: Property assignment with validators
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]))
def test_boolean_property_with_validator(value):
    """Test that boolean properties with validators work correctly"""
    obj = bedrock.Agent(title="TestAgent", AgentName="TestAgent")
    obj.AutoPrepare = value
    
    # The validator should have converted it to boolean
    expected = boolean(value)
    assert obj.AutoPrepare == expected


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_property_with_validator(value):
    """Test that double properties with validators work correctly"""
    obj = bedrock.Agent(title="TestAgent", AgentName="TestAgent")
    obj.IdleSessionTTLInSeconds = value
    assert obj.IdleSessionTTLInSeconds == value


# Test 7: to_dict serialization
def test_to_dict_basic():
    """Test that to_dict produces expected structure"""
    obj = bedrock.S3Identifier()
    obj.S3BucketName = "my-bucket"
    obj.S3ObjectKey = "my-key"
    
    result = obj.to_dict()
    assert isinstance(result, dict)
    assert result.get("S3BucketName") == "my-bucket"
    assert result.get("S3ObjectKey") == "my-key"


@given(st.text(min_size=1), st.text(min_size=1))
def test_to_dict_preserves_values(bucket, key):
    """Test that to_dict preserves property values"""
    obj = bedrock.S3Identifier()
    obj.S3BucketName = bucket
    obj.S3ObjectKey = key
    
    result = obj.to_dict()
    assert result.get("S3BucketName") == bucket
    assert result.get("S3ObjectKey") == key


if __name__ == "__main__":
    print("Running property-based tests for troposphere.bedrock...")
    pytest.main([__file__, "-v"])