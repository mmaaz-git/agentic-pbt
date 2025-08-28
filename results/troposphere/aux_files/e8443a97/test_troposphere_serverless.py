#!/usr/bin/env python3
"""Property-based tests for troposphere.serverless validators."""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest
import troposphere.serverless as serverless


# Test 1: boolean() function - test conversion properties
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_valid_conversions(value):
    """Test that boolean() correctly converts documented truthy/falsy values."""
    result = serverless.boolean(value)
    
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_inputs_raise(value):
    """Test that boolean() raises ValueError for non-boolean-like inputs."""
    with pytest.raises(ValueError):
        serverless.boolean(value)


# Test 2: integer() function - test integer validation
@given(st.integers())
def test_integer_accepts_int(value):
    """Test that integer() accepts actual integers."""
    result = serverless.integer(value)
    assert result == value


@given(st.text(min_size=1).map(str))
def test_integer_string_conversion(value):
    """Test that integer() handles string representations correctly."""
    try:
        int(value)  # Can Python convert it?
        result = serverless.integer(value)
        assert result == value  # Should return original string
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            serverless.integer(value)


@given(st.floats())
def test_integer_float_handling(value):
    """Test integer() behavior with floats."""
    if value.is_integer() and not math.isnan(value) and not math.isinf(value):
        # Integer-valued floats might work
        try:
            result = serverless.integer(value)
            assert int(result) == int(value)
        except ValueError:
            pass  # Some implementations may still reject
    else:
        # Non-integer floats should fail
        with pytest.raises(ValueError):
            serverless.integer(value)


# Test 3: positive_integer() function
@given(st.integers())
def test_positive_integer_sign_check(value):
    """Test that positive_integer() correctly validates sign."""
    if value >= 0:
        result = serverless.positive_integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            serverless.positive_integer(value)


# Test 4: integer_range() factory function
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-2000, max_value=2000)
)
def test_integer_range_bounds(min_val, max_val, test_val):
    """Test that integer_range() correctly enforces bounds."""
    assume(min_val <= max_val)  # Valid range
    
    validator = serverless.integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        with pytest.raises(ValueError) as exc_info:
            validator(test_val)
        assert "between" in str(exc_info.value)


# Test 5: validate_memory_size() - Lambda memory constraints
@given(st.integers(min_value=-1000, max_value=20000))
def test_validate_memory_size_range(value):
    """Test Lambda memory size validation (128-10240 MB)."""
    MINIMUM_MEMORY = 128
    MAXIMUM_MEMORY = 10240
    
    if value < 0:
        # Negative values should fail in positive_integer
        with pytest.raises(ValueError):
            serverless.validate_memory_size(value)
    elif MINIMUM_MEMORY <= value <= MAXIMUM_MEMORY:
        result = serverless.validate_memory_size(value)
        assert result == value
    else:
        # Out of Lambda's memory range
        with pytest.raises(ValueError) as exc_info:
            serverless.validate_memory_size(value)
        if value >= 0:  # Only check message if it passes positive check
            assert "128" in str(exc_info.value) and "10240" in str(exc_info.value)


# Test 6: Enum validators (primary_key_type, starting_position, etc.)
@given(st.text())
def test_primary_key_type_validator(value):
    """Test DynamoDB primary key type validation."""
    valid_types = ["String", "Number", "Binary"]
    
    if value in valid_types:
        result = serverless.primary_key_type_validator(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            serverless.primary_key_type_validator(value)
        assert "KeyType must be one of" in str(exc_info.value)


@given(st.text())
def test_starting_position_validator(value):
    """Test Kinesis starting position validation."""
    valid_positions = ["TRIM_HORIZON", "LATEST"]
    
    if value in valid_positions:
        result = serverless.starting_position_validator(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            serverless.starting_position_validator(value)
        assert "StartingPosition must be one of" in str(exc_info.value)


@given(st.text())
def test_validate_package_type(value):
    """Test Lambda package type validation."""
    valid_types = ["Image", "Zip"]
    
    if value in valid_types:
        result = serverless.validate_package_type(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            serverless.validate_package_type(value)
        assert "PackageType must be one of" in str(exc_info.value)


# Test 7: double() function - float validation
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
))
def test_double_validation(value):
    """Test that double() validates float-convertible values."""
    try:
        float(value)
        result = serverless.double(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError) as exc_info:
            serverless.double(value)
        assert "not a valid double" in str(exc_info.value)


# Test 8: Edge cases and special values
def test_integer_range_inverted_bounds():
    """Test integer_range with min > max."""
    validator = serverless.integer_range(100, 50)  # min > max
    
    # This creates an impossible range - all values should fail
    with pytest.raises(ValueError):
        validator(75)  # In between but range is inverted
    with pytest.raises(ValueError):
        validator(50)  # Equal to "max"
    with pytest.raises(ValueError):
        validator(100)  # Equal to "min"


def test_positive_integer_zero():
    """Test that positive_integer accepts zero (it's non-negative)."""
    result = serverless.positive_integer(0)
    assert result == 0


def test_boolean_case_sensitivity():
    """Test case sensitivity in boolean conversions."""
    # These should work
    assert serverless.boolean("true") is True
    assert serverless.boolean("True") is True
    assert serverless.boolean("false") is False
    assert serverless.boolean("False") is False
    
    # These should fail
    with pytest.raises(ValueError):
        serverless.boolean("TRUE")
    with pytest.raises(ValueError):
        serverless.boolean("FALSE")
    with pytest.raises(ValueError):
        serverless.boolean("TrUe")