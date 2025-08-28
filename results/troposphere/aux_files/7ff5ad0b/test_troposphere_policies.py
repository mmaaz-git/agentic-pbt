"""Property-based tests for troposphere.policies module"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import troposphere.policies as policies


# Test 1: Boolean validator round-trip property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles all documented valid inputs"""
    result = policies.boolean(value)
    assert isinstance(result, bool)
    
    # Values that should be True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Values that should be False  
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    # Skip valid inputs
    assume(value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"])
    
    with pytest.raises(ValueError):
        policies.boolean(value)


# Test 2: positive_integer invariant
@given(st.integers())
def test_positive_integer_validator(value):
    """Test that positive_integer only accepts non-negative integers"""
    if value >= 0:
        result = policies.positive_integer(value)
        assert result == value
        # Verify it can be converted to int
        assert int(result) >= 0
    else:
        with pytest.raises(ValueError) as exc_info:
            policies.positive_integer(value)
        assert "is not a positive integer" in str(exc_info.value)


@given(st.text())
def test_positive_integer_with_strings(value):
    """Test positive_integer with string inputs"""
    try:
        int_val = int(value)
        if int_val >= 0:
            result = policies.positive_integer(value)
            assert result == value
        else:
            with pytest.raises(ValueError):
                policies.positive_integer(value)
    except ValueError:
        # If string can't be converted to int, should raise ValueError
        with pytest.raises(ValueError):
            policies.positive_integer(value)


# Test 3: validate_pausetime format validation
@given(st.text())
def test_validate_pausetime_format(value):
    """Test that validate_pausetime only accepts PT-prefixed strings"""
    if value.startswith("PT"):
        result = policies.validate_pausetime(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            policies.validate_pausetime(value)
        assert "PauseTime should look like PT#H#M#S" in str(exc_info.value)


# Test 4: Property class validation with type mismatches
@given(st.text())
def test_codedeploy_lambda_alias_update_property_types(app_name):
    """Test CodeDeployLambdaAliasUpdate with string inputs for ApplicationName"""
    # This class has a bug: ApplicationName uses boolean validator but should accept strings
    obj = policies.CodeDeployLambdaAliasUpdate()
    
    # ApplicationName is marked as (boolean, True) but AWS expects a string
    # This should reveal the bug
    with pytest.raises(ValueError):
        obj.ApplicationName = app_name


@given(st.sampled_from([True, False, "true", "false", "True", "False", 1, 0]))  
def test_codedeploy_lambda_alias_boolean_fields_accept_boolean_like(value):
    """Test that boolean-validated fields in CodeDeployLambdaAliasUpdate accept boolean-like values"""
    obj = policies.CodeDeployLambdaAliasUpdate()
    
    # These fields use boolean validator - they should accept boolean-like values
    obj.ApplicationName = value
    obj.DeploymentGroupName = value
    
    # The values should be converted to boolean
    assert isinstance(obj.ApplicationName, bool)
    assert isinstance(obj.DeploymentGroupName, bool)


# Test 5: Integer validator edge cases
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.integers()
))
def test_integer_validator(value):
    """Test integer validator with various inputs"""
    try:
        int(value)
        result = policies.integer(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError) as exc_info:
            policies.integer(value)
        assert "is not a valid integer" in str(exc_info.value)


# Test 6: Test property instantiation with valid and invalid data
@given(
    count=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
    timeout=st.one_of(st.none(), st.text())
)
def test_resource_signal_properties(count, timeout):
    """Test ResourceSignal class with various inputs"""
    obj = policies.ResourceSignal()
    
    # Test Count property (positive_integer validator)
    if count is not None:
        if count >= 0:
            obj.Count = count
            assert obj.Count == count
        else:
            with pytest.raises(ValueError):
                obj.Count = count
    
    # Test Timeout property (validate_pausetime validator)
    if timeout is not None:
        if timeout.startswith("PT"):
            obj.Timeout = timeout
            assert obj.Timeout == timeout
        else:
            with pytest.raises(ValueError):
                obj.Timeout = timeout


# Test 7: Check that positive_integer actually rejects negative zero representations
@given(st.sampled_from(["-0", "-00", "-000"]))
def test_positive_integer_negative_zero_strings(value):
    """Test that positive_integer handles negative zero string representations"""
    # These should be treated as 0 and accepted
    result = policies.positive_integer(value)
    assert result == value
    assert int(result) == 0