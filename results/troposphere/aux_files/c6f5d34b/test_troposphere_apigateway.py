#!/usr/bin/env python3
import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the site-packages path to find troposphere
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.apigateway as apigateway
from troposphere.validators.apigateway import (
    dict_or_string,
    validate_timeout_in_millis,
    validate_authorizer_ttl,
    validate_gateway_response_type,
    validate_model,
)
from troposphere.validators import (
    boolean,
    positive_integer,
    integer,
    double,
    json_checker,
)


# Test 1: validate_timeout_in_millis should reject values < 50
@given(st.integers(min_value=-1000000, max_value=49))
def test_timeout_in_millis_rejects_below_50(value):
    """TimeoutInMillis validator should reject values below 50ms"""
    with pytest.raises(ValueError) as exc_info:
        validate_timeout_in_millis(value)
    assert "must be greater than 50" in str(exc_info.value)


@given(st.integers(min_value=50, max_value=1000000))
def test_timeout_in_millis_accepts_valid_values(value):
    """TimeoutInMillis validator should accept values >= 50"""
    result = validate_timeout_in_millis(value)
    assert result == value


# Test 2: validate_authorizer_ttl should reject values > 3600 and negative values
@given(st.integers(min_value=3601, max_value=1000000))
def test_authorizer_ttl_rejects_above_3600(value):
    """AuthorizerResultTtlInSeconds should reject values > 3600"""
    with pytest.raises(ValueError) as exc_info:
        validate_authorizer_ttl(value)
    assert "should be <= 3600" in str(exc_info.value)


@given(st.integers(min_value=-1000000, max_value=-1))
def test_authorizer_ttl_rejects_negative(value):
    """AuthorizerResultTtlInSeconds should reject negative values"""
    with pytest.raises(ValueError):
        validate_authorizer_ttl(value)


@given(st.integers(min_value=0, max_value=3600))
def test_authorizer_ttl_accepts_valid_values(value):
    """AuthorizerResultTtlInSeconds should accept 0 <= value <= 3600"""
    result = validate_authorizer_ttl(value)
    assert result == value


# Test 3: dict_or_string type validation
@given(st.one_of(st.dictionaries(st.text(), st.text()), st.text()))
def test_dict_or_string_accepts_valid_types(value):
    """dict_or_string should accept dicts and strings"""
    result = dict_or_string(value)
    assert result == value


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.lists(st.text()),
    st.booleans(),
    st.none()
))
def test_dict_or_string_rejects_invalid_types(value):
    """dict_or_string should reject non-dict, non-string types"""
    with pytest.raises(TypeError) as exc_info:
        dict_or_string(value)
    assert "must be either dict or str" in str(exc_info.value)


# Test 4: validate_gateway_response_type enum validation
@given(st.sampled_from([
    "ACCESS_DENIED", "API_CONFIGURATION_ERROR", "AUTHORIZER_FAILURE",
    "AUTHORIZER_CONFIGURATION_ERROR", "BAD_REQUEST_PARAMETERS",
    "BAD_REQUEST_BODY", "DEFAULT_4XX", "DEFAULT_5XX", "EXPIRED_TOKEN",
    "INVALID_SIGNATURE", "INTEGRATION_FAILURE", "INTEGRATION_TIMEOUT",
    "INVALID_API_KEY", "MISSING_AUTHENTICATION_TOKEN", "QUOTA_EXCEEDED",
    "REQUEST_TOO_LARGE", "RESOURCE_NOT_FOUND", "THROTTLED",
    "UNAUTHORIZED", "UNSUPPORTED_MEDIA_TYPE"
]))
def test_gateway_response_type_accepts_valid_types(value):
    """Gateway response type should accept valid response types"""
    result = validate_gateway_response_type(value)
    assert result == value


@given(st.text().filter(lambda x: x not in [
    "ACCESS_DENIED", "API_CONFIGURATION_ERROR", "AUTHORIZER_FAILURE",
    "AUTHORIZER_CONFIGURATION_ERROR", "BAD_REQUEST_PARAMETERS",
    "BAD_REQUEST_BODY", "DEFAULT_4XX", "DEFAULT_5XX", "EXPIRED_TOKEN",
    "INVALID_SIGNATURE", "INTEGRATION_FAILURE", "INTEGRATION_TIMEOUT",
    "INVALID_API_KEY", "MISSING_AUTHENTICATION_TOKEN", "QUOTA_EXCEEDED",
    "REQUEST_TOO_LARGE", "RESOURCE_NOT_FOUND", "THROTTLED",
    "UNAUTHORIZED", "UNSUPPORTED_MEDIA_TYPE"
]))
def test_gateway_response_type_rejects_invalid_types(value):
    """Gateway response type should reject invalid response types"""
    with pytest.raises(ValueError) as exc_info:
        validate_gateway_response_type(value)
    assert "is not a valid ResponseType" in str(exc_info.value)


# Test 5: boolean validator conversion
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_converts_to_true(value):
    """Boolean validator should convert truthy values to True"""
    result = boolean(value)
    assert result is True
    assert isinstance(result, bool)


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_converts_to_false(value):
    """Boolean validator should convert falsy values to False"""
    result = boolean(value)
    assert result is False
    assert isinstance(result, bool)


@given(st.one_of(
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(allow_nan=False),
    st.none()
))
def test_boolean_rejects_invalid_values(value):
    """Boolean validator should reject non-boolean convertible values"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 6: positive_integer validator
@given(st.integers(min_value=0, max_value=1000000))
def test_positive_integer_accepts_non_negative(value):
    """positive_integer should accept values >= 0"""
    result = positive_integer(value)
    assert result == value


@given(st.integers(min_value=-1000000, max_value=-1))
def test_positive_integer_rejects_negative(value):
    """positive_integer should reject negative values"""
    with pytest.raises(ValueError) as exc_info:
        positive_integer(value)
    assert "is not a positive integer" in str(exc_info.value)


# Test for string representations of integers
@given(st.integers(min_value=0, max_value=1000000))
def test_positive_integer_accepts_string_numbers(value):
    """positive_integer should accept string representations of non-negative integers"""
    str_value = str(value)
    result = positive_integer(str_value)
    assert result == str_value
    assert int(result) == value


# Test 7: json_checker validator
@given(st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.booleans())))
def test_json_checker_converts_dict_to_string(value):
    """json_checker should convert dicts to JSON strings"""
    result = json_checker(value)
    assert isinstance(result, str)
    # Should be valid JSON that can be parsed back
    parsed = json.loads(result)
    assert parsed == value


@given(st.text())
@settings(max_examples=100)
def test_json_checker_validates_json_strings(value):
    """json_checker should validate JSON strings"""
    # Only test with valid JSON strings
    try:
        json.loads(value)
        is_valid_json = True
    except (json.JSONDecodeError, ValueError):
        is_valid_json = False
    
    if is_valid_json:
        result = json_checker(value)
        assert result == value
    else:
        with pytest.raises(json.JSONDecodeError):
            json_checker(value)


# Test 8: integer validator
@given(st.one_of(st.integers(), st.text().filter(lambda x: x.lstrip('-').isdigit())))
def test_integer_accepts_valid_integers(value):
    """integer validator should accept integers and their string representations"""
    result = integer(value)
    assert result == value
    int(result)  # Should be convertible to int


@given(st.one_of(
    st.text().filter(lambda x: not x.lstrip('-').replace('.', '', 1).isdigit()),
    st.floats(allow_nan=False).filter(lambda x: x != int(x)),
    st.none()
))
def test_integer_rejects_non_integers(value):
    """integer validator should reject non-integer values"""
    assume(value != "")  # Empty string case
    try:
        int(value)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if not can_convert:
        with pytest.raises(ValueError) as exc_info:
            integer(value)
        assert "is not a valid integer" in str(exc_info.value)


# Test 9: double validator
@given(st.one_of(st.floats(allow_nan=False, allow_infinity=False), st.integers()))
def test_double_accepts_numeric_values(value):
    """double validator should accept floats and integers"""
    result = double(value)
    assert result == value
    float(result)  # Should be convertible to float


@given(st.text())
@settings(max_examples=100)
def test_double_accepts_numeric_strings(value):
    """double validator should accept string representations of numbers"""
    try:
        float(value)
        is_numeric = True
    except (ValueError, TypeError):
        is_numeric = False
    
    if is_numeric:
        result = double(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            double(value)
        assert "is not a valid double" in str(exc_info.value)


# Test Model.validate() with json_checker
@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_model_validate_with_dict_schema(schema):
    """Model should accept dict schemas and convert them to JSON strings"""
    model = apigateway.Model("TestModel", RestApiId="test-api")
    model.Schema = schema
    model.validate()
    # After validation, schema should be a JSON string
    assert isinstance(model.properties.get("Schema"), str)
    parsed = json.loads(model.properties["Schema"])
    assert parsed == schema


@given(st.text())
@settings(max_examples=100)
def test_model_validate_with_string_schema(schema):
    """Model should validate JSON string schemas"""
    model = apigateway.Model("TestModel", RestApiId="test-api")
    model.Schema = schema
    
    try:
        json.loads(schema)
        is_valid_json = True
    except (json.JSONDecodeError, ValueError):
        is_valid_json = False
    
    if is_valid_json:
        model.validate()
        assert model.properties.get("Schema") == schema
    else:
        with pytest.raises(json.JSONDecodeError):
            model.validate()


if __name__ == "__main__":
    print("Running property-based tests for troposphere.apigateway validators...")
    pytest.main([__file__, "-v"])