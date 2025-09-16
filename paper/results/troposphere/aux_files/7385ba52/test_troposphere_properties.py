#!/usr/bin/env python3
"""Property-based tests for troposphere module using Hypothesis."""

import json
import re
import sys
import os
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere environment to the path
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

# Now import troposphere modules
import troposphere
from troposphere import validators
from troposphere import Tags, Tag, BaseAWSObject, encode_to_dict


# Test 1: s3_bucket_name validator
@given(st.text(min_size=1, max_size=100))
def test_s3_bucket_name_valid_buckets_dont_crash(name):
    """Test that valid S3 bucket names are accepted by the validator."""
    # Skip obviously invalid names to focus on edge cases
    if len(name) < 3 or len(name) > 63:
        assume(False)
    if not re.match(r"^[a-z0-9.-]+$", name):
        assume(False)
    if name.startswith("-") or name.endswith("-"):
        assume(False) 
    if name.startswith(".") or name.endswith("."):
        assume(False)
    if ".." in name:
        assume(False)
    # Check for IP address pattern
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", name):
        assume(False)
    
    try:
        result = validators.s3_bucket_name(name)
        # If it passes, result should equal input
        assert result == name
    except ValueError:
        # The validator rejected it - that's fine for this test
        pass


@given(st.from_regex(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"))
def test_s3_bucket_name_rejects_ip_addresses(ip_like):
    """S3 bucket names that look like IP addresses should be rejected."""
    with pytest.raises(ValueError, match="is not a valid s3 bucket name"):
        validators.s3_bucket_name(ip_like)


@given(st.text(min_size=2, max_size=63).filter(lambda x: ".." in x))
def test_s3_bucket_name_rejects_consecutive_dots(name):
    """S3 bucket names with consecutive dots should be rejected."""
    with pytest.raises(ValueError, match="is not a valid s3 bucket name"):
        validators.s3_bucket_name(name)


# Test 2: network_port validator
@given(st.integers())
def test_network_port_range(port):
    """Network ports must be between -1 and 65535."""
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            validators.network_port(port)


@given(st.integers(min_value=-1, max_value=65535))
def test_network_port_valid_range_accepted(port):
    """Valid network ports should be accepted."""
    result = validators.network_port(port)
    assert result == port


# Test 3: boolean validator
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_values(value):
    """All true-like values should return True."""
    result = validators.boolean(value)
    assert result is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_false_values(value):
    """All false-like values should return False."""
    result = validators.boolean(value)
    assert result is False


@given(st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]))
def test_boolean_invalid_strings_raise(value):
    """Invalid string values should raise ValueError."""
    with pytest.raises(ValueError):
        validators.boolean(value)


# Test 4: positive_integer validator
@given(st.integers())
def test_positive_integer_validator(num):
    """positive_integer should accept non-negative integers only."""
    if num >= 0:
        result = validators.positive_integer(num)
        assert result == num
    else:
        with pytest.raises(ValueError, match="is not a positive integer"):
            validators.positive_integer(num)


# Test 5: json_checker round-trip property
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=100)
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5)
        ),
        max_leaves=20
    ),
    max_size=10
))
def test_json_checker_dict_round_trip(data):
    """json_checker should convert dict to JSON string and be parseable back."""
    result = validators.json_checker(data)
    assert isinstance(result, str)
    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed == data


@given(st.text(min_size=1))
def test_json_checker_string_validation(text):
    """json_checker should validate JSON strings."""
    try:
        # Try to parse as JSON
        json.loads(text)
        is_valid_json = True
    except (json.JSONDecodeError, ValueError):
        is_valid_json = False
    
    if is_valid_json:
        result = validators.json_checker(text)
        assert result == text
    else:
        # Invalid JSON strings should be passed through
        # (the function only validates, doesn't reject invalid JSON strings)
        try:
            result = validators.json_checker(text)
            # If it returns, it should have validated it
            json.loads(result)
        except (json.JSONDecodeError, ValueError):
            pass  # This is expected for invalid JSON


# Test 6: Tags concatenation
@given(
    st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50), min_size=1, max_size=5),
    st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50), min_size=1, max_size=5)
)
def test_tags_concatenation_preserves_all_tags(tags1, tags2):
    """Tags concatenation should preserve all tags from both objects."""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    combined = t1 + t2
    
    # Convert to dict for comparison
    combined_dict = combined.to_dict()
    
    # All tags from t1 should be in combined
    t1_dict = t1.to_dict()
    for tag in t1_dict:
        assert tag in combined_dict
    
    # All tags from t2 should be in combined
    t2_dict = t2.to_dict()
    for tag in t2_dict:
        assert tag in combined_dict
    
    # Combined should have the right number of tags
    assert len(combined_dict) == len(t1_dict) + len(t2_dict)


# Test 7: encode_to_dict function
@given(st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=50)
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=3),
        st.tuples(children, children)
    ),
    max_leaves=10
))
def test_encode_to_dict_preserves_structure(data):
    """encode_to_dict should preserve data structure for basic types."""
    result = encode_to_dict(data)
    
    # For basic types, should be unchanged
    if isinstance(data, (type(None), bool, int, float, str)):
        assert result == data
    # Lists and tuples become lists
    elif isinstance(data, (list, tuple)):
        assert isinstance(result, list)
        assert len(result) == len(data)
    # Dicts remain dicts
    elif isinstance(data, dict):
        assert isinstance(result, dict)
        assert set(result.keys()) == set(data.keys())


# Test 8: validate_title regex pattern
@given(st.text(min_size=1, max_size=50))
def test_validate_title_alphanumeric_only(title):
    """BaseAWSObject.validate_title should only accept alphanumeric titles."""
    # Create a minimal object to test
    class TestObject(BaseAWSObject):
        pass
    
    is_alphanumeric = bool(re.match(r"^[a-zA-Z0-9]+$", title))
    
    if is_alphanumeric:
        # Should not raise
        obj = TestObject(title=title, validation=True)
        assert obj.title == title
    else:
        # Should raise ValueError
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            TestObject(title=title, validation=True)


# Test 9: integer_range validator factory
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.integers()
)
def test_integer_range_validator(min_val, max_val, test_val):
    """integer_range should create validators that enforce min/max bounds."""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = validators.integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


# Test 10: validate_delimiter
@given(st.one_of(st.text(), st.integers(), st.none(), st.lists(st.text())))
def test_validate_delimiter(delimiter):
    """validate_delimiter should only accept strings."""
    from troposphere import validate_delimiter
    
    if isinstance(delimiter, str):
        # Should not raise
        validate_delimiter(delimiter)
    else:
        # Should raise ValueError
        with pytest.raises(ValueError, match="Delimiter must be a String"):
            validate_delimiter(delimiter)


# Test 11: validate_pausetime
@given(st.text(min_size=1, max_size=20))
def test_validate_pausetime(pausetime):
    """validate_pausetime should only accept strings starting with 'PT'."""
    from troposphere import validate_pausetime
    
    if pausetime.startswith("PT"):
        result = validate_pausetime(pausetime)
        assert result == pausetime
    else:
        with pytest.raises(ValueError, match="PauseTime should look like PT#H#M#S"):
            validate_pausetime(pausetime)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])