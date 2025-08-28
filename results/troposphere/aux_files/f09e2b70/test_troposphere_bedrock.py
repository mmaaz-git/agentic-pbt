"""Property-based tests for troposphere.bedrock validators"""

import sys
import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import (
    boolean, integer, positive_integer, double, 
    network_port, s3_bucket_name, elb_name,
    integer_range, json_checker
)
import json


# Test 1: Boolean validator idempotence property
@given(st.sampled_from([True, False, 1, 0, "true", "True", "false", "False", "1", "0"]))
def test_boolean_idempotence(value):
    """If boolean() accepts a value, calling it again on the result should be idempotent"""
    result = boolean(value)
    assert boolean(result) == result
    assert isinstance(result, bool)


# Test 2: Boolean validator handles all documented valid inputs
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_valid_inputs(value):
    """Boolean should handle all documented valid inputs correctly"""
    result = boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 3: Integer validator consistency
@given(st.one_of(
    st.integers(),
    st.text(alphabet=st.characters(whitelist_categories=["Nd"]), min_size=1),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_validator_consistency(value):
    """If integer(x) succeeds, int(x) must also succeed with same value"""
    try:
        result = integer(value)
        int_value = int(value)
        # The validator should preserve the ability to convert to int
        assert int(result) == int_value
    except ValueError:
        # Both should fail
        with pytest.raises(ValueError):
            integer(value)


# Test 4: Positive integer invariant
@given(st.integers())
def test_positive_integer_invariant(value):
    """positive_integer should only accept non-negative integers"""
    if value >= 0:
        result = positive_integer(value)
        assert int(result) >= 0
    else:
        with pytest.raises(ValueError):
            positive_integer(value)


# Test 5: Double validator consistency
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet=st.characters(whitelist_categories=["Nd"]), min_size=1)
))
def test_double_validator_consistency(value):
    """If double(x) succeeds, float(x) must also succeed"""
    try:
        result = double(value)
        float_value = float(value)
        # The validator should preserve the ability to convert to float
        assert float(result) == float_value
    except (ValueError, TypeError):
        # Both should fail
        with pytest.raises(ValueError):
            double(value)


# Test 6: Network port range invariant
@given(st.integers())
def test_network_port_range_invariant(value):
    """network_port must enforce valid port range -1 to 65535"""
    if -1 <= value <= 65535:
        result = network_port(value)
        assert int(result) == value
    else:
        with pytest.raises(ValueError) as exc_info:
            network_port(value)
        assert "between 0 and 65535" in str(exc_info.value)


# Test 7: S3 bucket name validation - no consecutive periods
@given(st.text(alphabet=st.characters(whitelist_categories=["Ll", "Nd"]), min_size=3, max_size=63))
def test_s3_bucket_consecutive_periods(name):
    """S3 bucket names with consecutive periods should be rejected"""
    if ".." in name:
        with pytest.raises(ValueError) as exc_info:
            s3_bucket_name(name)
        assert "not a valid s3 bucket name" in str(exc_info.value)
    else:
        # Skip test if it doesn't match other requirements
        pass


# Test 8: S3 bucket name - IP address rejection
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_s3_bucket_ip_address_rejection(a, b, c, d):
    """S3 bucket names that look like IP addresses should be rejected"""
    ip_like_name = f"{a}.{b}.{c}.{d}"
    with pytest.raises(ValueError) as exc_info:
        s3_bucket_name(ip_like_name)
    assert "not a valid s3 bucket name" in str(exc_info.value)


# Test 9: Integer range validator bounds checking
@given(
    st.integers(min_value=-1000, max_value=1000),  # min
    st.integers(min_value=-1000, max_value=1000),  # max
    st.integers(min_value=-2000, max_value=2000)   # value to test
)
def test_integer_range_bounds(min_val, max_val, test_value):
    """integer_range should correctly enforce min/max bounds"""
    assume(min_val <= max_val)  # Valid range
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_value <= max_val:
        result = validator(test_value)
        assert int(result) == test_value
    else:
        with pytest.raises(ValueError) as exc_info:
            validator(test_value)
        assert "Integer must be between" in str(exc_info.value)


# Test 10: JSON checker round-trip property
@given(st.one_of(
    st.dictionaries(
        st.text(min_size=1),
        st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text()
            ),
            lambda children: st.one_of(
                st.lists(children),
                st.dictionaries(st.text(min_size=1), children)
            ),
            max_leaves=10
        )
    ),
    st.text().map(lambda x: json.dumps({"key": x}))  # JSON strings
))
def test_json_checker_round_trip(value):
    """json_checker should handle dict to JSON string conversion correctly"""
    if isinstance(value, dict):
        result = json_checker(value)
        assert isinstance(result, str)
        # Should be valid JSON that parses back to original
        assert json.loads(result) == value
    elif isinstance(value, str):
        # Should validate it's proper JSON
        result = json_checker(value)
        assert result == value
        json.loads(result)  # Should not raise


# Test 11: ELB name validation pattern
@given(st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=32))
def test_elb_name_pattern(name):
    """Test ELB name validation against its regex pattern"""
    # ELB names must start with alphanumeric, can contain hyphens, and end with alphanumeric
    elb_pattern = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$")
    
    if elb_pattern.match(name):
        result = elb_name(name)
        assert result == name
    else:
        with pytest.raises(ValueError) as exc_info:
            elb_name(name)
        assert "not a valid elb name" in str(exc_info.value)


# Test 12: Boolean validator invalid input handling
@given(st.one_of(
    st.text().filter(lambda x: x not in ["true", "True", "false", "False", "1", "0"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none()
))
def test_boolean_invalid_inputs(value):
    """Boolean validator should reject invalid inputs"""
    with pytest.raises(ValueError):
        boolean(value)


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])