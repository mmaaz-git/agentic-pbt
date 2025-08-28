"""Additional property-based tests for edge cases in troposphere.validators."""

import json
from hypothesis import assume, given, strategies as st, settings, example
import troposphere.validators as validators
import pytest
import math


# Test for potential overflow/underflow issues in positive_integer
@given(st.one_of(
    st.just(0),
    st.just(-0),
    st.just(0.0),
    st.just(-0.0),
    st.text().filter(lambda x: x.strip() == "0" if x.strip() else False),
    st.text().filter(lambda x: x.strip() == "-0" if x.strip() else False)
))
def test_positive_integer_zero_edge_cases(value):
    """Test positive_integer with various representations of zero."""
    try:
        result = validators.positive_integer(value)
        # If it succeeds, it should return something that converts to 0
        assert int(result) == 0
    except (ValueError, TypeError):
        # Some representations might not be valid integers
        pass


# Test for string representations in integer function
@given(st.text())
def test_integer_string_handling(value):
    """Test how integer function handles various string inputs."""
    try:
        result = validators.integer(value)
        # If it succeeds, int(result) should equal int(value)
        assert int(result) == int(value)
    except (ValueError, TypeError):
        # Should fail for non-integer strings
        with pytest.raises(ValueError):
            validators.integer(value)


# Test for float inputs to positive_integer
@given(st.floats(min_value=-100, max_value=100))
def test_positive_integer_with_floats(value):
    """Test positive_integer behavior with float inputs."""
    if value >= 0 and value == int(value):
        result = validators.positive_integer(value)
        assert int(result) == int(value)
    elif value < 0:
        with pytest.raises(ValueError):
            validators.positive_integer(value)


# Edge case: Test network_port with -1 (special value)
def test_network_port_negative_one():
    """Test that network_port accepts -1 as specified in the code."""
    result = validators.network_port(-1)
    assert int(result) == -1


# Test network_port boundary values
@given(st.sampled_from([-2, -1, 0, 65535, 65536]))
def test_network_port_boundaries(port):
    """Test network_port at exact boundaries."""
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert int(result) == port
    else:
        with pytest.raises(ValueError):
            validators.network_port(port)


# Test s3_bucket_name with edge cases
@given(st.text(min_size=2, max_size=4).filter(lambda x: "." in x))
def test_s3_bucket_periods_edge_cases(name):
    """Test s3_bucket_name handling of periods."""
    # Names with ".." should fail
    if ".." in name:
        with pytest.raises(ValueError):
            validators.s3_bucket_name(name)
    # Single periods might be OK depending on other rules


# Test integer_range with equal min and max
@given(st.integers(min_value=-1000, max_value=1000))
def test_integer_range_single_value(value):
    """Test integer_range when min equals max."""
    checker = validators.integer_range(value, value)
    # Should only accept that exact value
    result = checker(value)
    assert int(result) == value
    
    # Should reject any other value
    if value != value + 1:
        with pytest.raises(ValueError):
            checker(value + 1)
    if value != value - 1:
        with pytest.raises(ValueError):
            checker(value - 1)


# Test json_checker with empty containers
@given(st.one_of(
    st.just({}),
    st.just([]),
    st.just("{}"),
    st.just("[]")
))
def test_json_checker_empty_containers(data):
    """Test json_checker with empty JSON structures."""
    result = validators.json_checker(data)
    if isinstance(data, str):
        assert result == data
    else:
        assert json.loads(result) == data


# Test boolean with numeric strings
@given(st.one_of(
    st.just("0.0"),
    st.just("1.0"),
    st.just("00"),
    st.just("01"),
    st.just("001"),
))
def test_boolean_numeric_string_edge_cases(value):
    """Test boolean with non-standard numeric string representations."""
    # These are not in the explicit list, so should raise ValueError
    with pytest.raises(ValueError):
        validators.boolean(value)


# Test for mutually_exclusive with overlapping properties
def test_mutually_exclusive_properties():
    """Test mutually_exclusive validator function."""
    # Test case where multiple properties are specified
    properties = {"prop1": "value1", "prop2": "value2", "prop3": None}
    
    # Should raise error if more than one specified
    with pytest.raises(ValueError, match="only one of the following can be specified"):
        validators.mutually_exclusive("TestClass", properties, ["prop1", "prop2"])
    
    # Should not raise if only one specified
    result = validators.mutually_exclusive("TestClass", properties, ["prop1", "prop3"])
    assert result == 1


# Test exactly_one validator
def test_exactly_one_validator():
    """Test exactly_one validator function."""
    # Test case where no properties are specified
    properties = {"other": "value"}
    
    with pytest.raises(ValueError, match="one of the following must be specified"):
        validators.exactly_one("TestClass", properties, ["prop1", "prop2"])
    
    # Test case where exactly one is specified
    properties = {"prop1": "value", "other": "value"}
    result = validators.exactly_one("TestClass", properties, ["prop1", "prop2"])
    assert result == 1


# Test check_required validator
def test_check_required_validator():
    """Test check_required validator function."""
    properties = {"prop1": "value"}
    
    # Should raise if required property is missing
    with pytest.raises(ValueError, match="required in TestClass"):
        validators.check_required("TestClass", properties, ["prop1", "prop2"])
    
    # Should not raise if all required properties are present
    validators.check_required("TestClass", properties, ["prop1"])


# Test one_of validator
def test_one_of_validator():
    """Test one_of validator function."""
    properties = {"prop": "invalid"}
    
    # Should raise if value not in allowed list
    with pytest.raises(ValueError, match="must be one of"):
        validators.one_of("TestClass", properties, "prop", ["valid1", "valid2"])
    
    # Should not raise if value is valid
    properties = {"prop": "valid1"}
    validators.one_of("TestClass", properties, "prop", ["valid1", "valid2"])


# Test integer with very large numbers
@given(st.integers(min_value=10**100, max_value=10**101))
def test_integer_very_large_numbers(value):
    """Test integer validator with very large numbers."""
    result = validators.integer(value)
    assert int(result) == value


# Test double with special float values
@given(st.sampled_from([
    float('inf'),
    float('-inf'),
    float('nan')
]))
def test_double_special_values(value):
    """Test double validator with special float values."""
    if math.isnan(value):
        # NaN should work since float(nan) doesn't raise
        result = validators.double(value)
        assert math.isnan(float(result))
    else:
        # Infinity values should work
        result = validators.double(value)
        assert float(result) == value