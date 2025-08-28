"""Property-based tests for troposphere.elasticsearch module"""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest
import troposphere.validators as validators
import troposphere.validators.elasticsearch as es_validators


# Test 1: integer_range should properly validate boundaries
@given(
    min_val=st.integers(min_value=-1000, max_value=1000),
    max_val=st.integers(min_value=-1000, max_value=1000)
)
def test_integer_range_boundaries(min_val, max_val):
    """Test that integer_range correctly validates boundaries"""
    assume(min_val <= max_val)
    
    checker = es_validators.integer_range(min_val, max_val)
    
    # Property 1: Values within range should be accepted
    valid_value = (min_val + max_val) // 2 if min_val < max_val else min_val
    result = checker(valid_value)
    assert result == valid_value  # Should return original value
    
    # Property 2: Boundary values should be accepted
    assert checker(min_val) == min_val
    assert checker(max_val) == max_val
    
    # Property 3: Values outside range should raise ValueError
    if min_val > -1000:
        with pytest.raises(ValueError, match="Integer must be between"):
            checker(min_val - 1)
    
    if max_val < 1000:
        with pytest.raises(ValueError, match="Integer must be between"):
            checker(max_val + 1)


# Test 2: integer_range with string inputs
@given(
    min_val=st.integers(min_value=-100, max_value=100),
    max_val=st.integers(min_value=-100, max_value=100),
    value=st.integers(min_value=-200, max_value=200)
)
def test_integer_range_string_conversion(min_val, max_val, value):
    """Test that integer_range handles string representations of integers"""
    assume(min_val <= max_val)
    
    checker = es_validators.integer_range(min_val, max_val)
    str_value = str(value)
    
    if min_val <= value <= max_val:
        # Should accept and return the original string
        result = checker(str_value)
        assert result == str_value  # Returns original, not converted
    else:
        with pytest.raises(ValueError):
            checker(str_value)


# Test 3: boolean function idempotence and consistency
@given(st.sampled_from([
    True, False, 1, 0, "1", "0", "true", "false", "True", "False"
]))
def test_boolean_idempotence(value):
    """Test that boolean conversion is idempotent"""
    first_result = validators.boolean(value)
    # Applying boolean to its result should return the same value
    second_result = validators.boolean(first_result)
    assert first_result == second_result
    assert isinstance(first_result, bool)


# Test 4: boolean function completeness
@given(st.one_of(
    st.integers(),
    st.text(min_size=0, max_size=20),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans()
))
def test_boolean_coverage(value):
    """Test boolean function with various input types"""
    truthy_values = [True, 1, "1", "true", "True"]
    falsy_values = [False, 0, "0", "false", "False"]
    
    try:
        result = validators.boolean(value)
        # If it succeeds, value must be in one of the valid sets
        assert value in truthy_values or value in falsy_values
        if value in truthy_values:
            assert result is True
        else:
            assert result is False
    except ValueError:
        # If it fails, value must not be in either valid set
        assert value not in truthy_values
        assert value not in falsy_values


# Test 5: integer validator type preservation
@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789-", min_size=1, max_size=10)
))
def test_integer_type_preservation(value):
    """Test that integer validator preserves input type"""
    try:
        # Try to convert to int first to see if it should work
        int_val = int(value)
        # If conversion works, validator should succeed
        result = validators.integer(value)
        # Critical property: returns original value, not converted
        assert result == value
        assert result is value  # Should be the same object
    except (ValueError, TypeError):
        # If int() fails, validator should also fail
        with pytest.raises(ValueError):
            validators.integer(value)


# Test 6: integer validator with float strings
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_float_handling(float_val):
    """Test integer validator with float values"""
    # Integer validator should handle integer-valued floats
    if float_val == int(float_val):  # Is integer-valued
        # String representation might work
        try:
            result = validators.integer(str(int(float_val)))
            assert result == str(int(float_val))
        except ValueError:
            pass  # Some edge cases might fail
    
    # Direct float should work if integer-valued
    if float_val.is_integer():
        result = validators.integer(float_val)
        assert result == float_val


# Test 7: validate_volume_type exhaustiveness
@given(st.text(min_size=0, max_size=20))
def test_volume_type_validation(volume_type):
    """Test volume type validation is exhaustive"""
    valid_types = ("standard", "gp2", "gp3", "io1")
    
    try:
        result = es_validators.validate_volume_type(volume_type)
        # If it succeeds, must be valid type
        assert volume_type in valid_types
        assert result == volume_type  # Should return input unchanged
    except ValueError as e:
        # If it fails, must not be valid type
        assert volume_type not in valid_types
        assert "must be one of" in str(e)


# Test 8: validate_tls_security_policy exhaustiveness
@given(st.text(min_size=0, max_size=50))
def test_tls_policy_validation(policy):
    """Test TLS security policy validation"""
    valid_policies = (
        "Policy-Min-TLS-1-0-2019-07",
        "Policy-Min-TLS-1-2-2019-07",
        "Policy-Min-TLS-1-2-PFS-2023-10",
    )
    
    try:
        result = es_validators.validate_tls_security_policy(policy)
        assert policy in valid_policies
        assert result == policy
    except ValueError as e:
        assert policy not in valid_policies
        assert "must be one of" in str(e)


# Test 9: validate_automated_snapshot_start_hour range
@given(st.integers(min_value=-100, max_value=100))
def test_snapshot_hour_validation(hour):
    """Test snapshot hour validation (0-23)"""
    try:
        result = es_validators.validate_automated_snapshot_start_hour(hour)
        # Should only succeed for 0-23
        assert 0 <= hour <= 23
        assert result == hour
    except ValueError as e:
        # Should fail for values outside 0-23
        assert hour < 0 or hour > 23
        assert "Integer must be between 0 and 23" in str(e)


# Test 10: EBS options validation logic
class MockEBSOptions:
    def __init__(self, properties):
        self.properties = properties

@given(
    volume_type=st.sampled_from(["standard", "gp2", "gp3", "io1", None]),
    has_iops=st.booleans(),
    iops_value=st.integers(min_value=100, max_value=64000)
)
def test_ebs_options_validation(volume_type, has_iops, iops_value):
    """Test EBS options validation for io1 volumes"""
    properties = {}
    if volume_type:
        properties["VolumeType"] = volume_type
    if has_iops:
        properties["Iops"] = iops_value
    
    mock_obj = MockEBSOptions(properties)
    
    # Property: io1 requires Iops, others don't care
    if volume_type == "io1" and not has_iops:
        with pytest.raises(ValueError, match="Must specify Iops if VolumeType is 'io1'"):
            es_validators.validate_ebs_options(mock_obj)
    else:
        # Should not raise
        result = es_validators.validate_ebs_options(mock_obj)
        assert result is None  # Function doesn't return anything


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])