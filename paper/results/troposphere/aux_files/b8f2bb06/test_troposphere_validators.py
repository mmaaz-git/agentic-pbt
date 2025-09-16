"""Property-based tests for troposphere.validators module."""

import json
from hypothesis import assume, given, strategies as st, settings
import troposphere.validators as validators
import pytest


# Test 1: Boolean function idempotence
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(["0", "1", "true", "True", "false", "False"])
))
def test_boolean_idempotence(value):
    """Test that boolean(boolean(x)) == boolean(x) for valid inputs."""
    try:
        result1 = validators.boolean(value)
        result2 = validators.boolean(result1)
        assert result2 == result1
    except ValueError:
        # If it raises ValueError, that's expected for invalid inputs
        pass


# Test 2: Positive integer validation
@given(st.integers())
def test_positive_integer_accepts_non_negative(value):
    """Test that positive_integer correctly validates non-negative integers."""
    if value >= 0:
        result = validators.positive_integer(value)
        assert int(result) == value
    else:
        with pytest.raises(ValueError):
            validators.positive_integer(value)


# Test 3: Integer range boundary conditions
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-2000, max_value=2000)
)
def test_integer_range_boundaries(min_val, max_val, test_val):
    """Test that integer_range correctly handles boundary conditions."""
    assume(min_val <= max_val)  # Ensure valid range
    
    checker = validators.integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = checker(test_val)
        assert int(result) == test_val
    else:
        with pytest.raises(ValueError):
            checker(test_val)


# Test 4: Network port validation
@given(st.integers(min_value=-10, max_value=70000))
def test_network_port_range(port):
    """Test that network_port correctly validates port numbers."""
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert int(result) == port
    else:
        with pytest.raises(ValueError):
            validators.network_port(port)


# Test 5: JSON checker round-trip property for dicts
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    max_size=5
))
def test_json_checker_dict_roundtrip(data):
    """Test that json_checker correctly handles dict to JSON conversion."""
    result = validators.json_checker(data)
    # Result should be a JSON string
    assert isinstance(result, str)
    # Should be able to parse it back
    parsed = json.loads(result)
    assert parsed == data


# Test 6: JSON checker round-trip property for JSON strings
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    max_size=5
))
def test_json_checker_string_roundtrip(data):
    """Test that json_checker correctly handles JSON string input."""
    json_str = json.dumps(data)
    result = validators.json_checker(json_str)
    # Result should be the same JSON string
    assert result == json_str
    # Should be able to parse it
    parsed = json.loads(result)
    assert parsed == data


# Test 7: S3 bucket name validation - consecutive periods
@given(st.text(min_size=3, max_size=63))
def test_s3_bucket_consecutive_periods(name):
    """Test that s3_bucket_name rejects names with consecutive periods."""
    if ".." in name:
        with pytest.raises(ValueError, match="not a valid s3 bucket name"):
            validators.s3_bucket_name(name)
    # Note: There are other validation rules, so we can't assert success for all other cases


# Test 8: S3 bucket name validation - IP addresses
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_s3_bucket_ip_address(a, b, c, d):
    """Test that s3_bucket_name rejects IP addresses."""
    ip_string = f"{a}.{b}.{c}.{d}"
    with pytest.raises(ValueError, match="not a valid s3 bucket name"):
        validators.s3_bucket_name(ip_string)


# Test 9: ELB name validation pattern
@given(st.text(min_size=1, max_size=33))
def test_elb_name_length_constraints(name):
    """Test ELB name validation constraints."""
    # Based on the regex: ^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$
    # This means: start with alphanumeric, optional middle part with hyphens, end with alphanumeric
    # Total max length is 32 characters
    
    if len(name) > 32:
        with pytest.raises(ValueError):
            validators.elb_name(name)
    elif len(name) == 0:
        with pytest.raises(ValueError):
            validators.elb_name(name)


# Test 10: Integer function round-trip
@given(st.integers())
def test_integer_roundtrip(value):
    """Test that integer validator preserves integer values."""
    result = validators.integer(value)
    assert int(result) == value


# Test 11: Double function round-trip
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_roundtrip(value):
    """Test that double validator preserves float values."""
    result = validators.double(value)
    assert float(result) == value


# Test 12: Encoding validator
@given(st.text())
def test_encoding_validation(encoding_str):
    """Test that encoding validator only accepts valid encodings."""
    valid_encodings = ["plain", "base64"]
    if encoding_str in valid_encodings:
        result = validators.encoding(encoding_str)
        assert result == encoding_str
    else:
        with pytest.raises(ValueError, match="Encoding needs to be one of"):
            validators.encoding(encoding_str)


# Test 13: WAF action type validation
@given(st.text())
def test_waf_action_type(action):
    """Test that waf_action_type only accepts valid actions."""
    valid_actions = ["ALLOW", "BLOCK", "COUNT"]
    if action in valid_actions:
        result = validators.waf_action_type(action)
        assert result == action
    else:
        with pytest.raises(ValueError, match="Type must be one of"):
            validators.waf_action_type(action)


# Test 14: Integer list item validator
@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10),
    st.integers(min_value=-200, max_value=200)
)
def test_integer_list_item(allowed_values, test_value):
    """Test that integer_list_item correctly validates against allowed values."""
    checker = validators.integer_list_item(allowed_values)
    
    if test_value in allowed_values:
        result = checker(test_value)
        assert int(result) == test_value
    else:
        with pytest.raises(ValueError, match="Integer must be one of following"):
            checker(test_value)


# Test 15: Testing edge case for positive_integer with 0
@given(st.just(0))
def test_positive_integer_accepts_zero(value):
    """Test that positive_integer accepts 0 as valid."""
    result = validators.positive_integer(value)
    assert int(result) == 0


# Test 16: Testing boolean with various string representations
@given(st.sampled_from([
    True, 1, "1", "true", "True",
    False, 0, "0", "false", "False"
]))
def test_boolean_known_values(value):
    """Test that boolean correctly handles all documented values."""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False