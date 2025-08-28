"""More aggressive property tests for troposphere.elasticsearch edge cases"""

import sys
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.validators as validators
import troposphere.validators.elasticsearch as es_validators


# Test edge case: Very large integers
@given(st.integers(min_value=sys.maxsize - 100, max_value=sys.maxsize + 100))
def test_integer_validator_large_values(value):
    """Test integer validator with very large values"""
    # The validator should handle large integers
    result = validators.integer(value)
    assert result == value
    
    # Also test with string representation
    str_val = str(value)
    result = validators.integer(str_val)
    assert result == str_val


# Test edge case: integer_range with float boundaries
@given(
    min_float=st.floats(min_value=-100.5, max_value=100.5, allow_nan=False),
    max_float=st.floats(min_value=-100.5, max_value=100.5, allow_nan=False),
    test_val=st.floats(min_value=-200, max_value=200, allow_nan=False)
)
def test_integer_range_float_boundaries(min_float, max_float, test_val):
    """Test integer_range when boundaries are floats"""
    assume(min_float <= max_float)
    
    # integer_range should work with float boundaries
    checker = es_validators.integer_range(min_float, max_float)
    
    # Test with integer value
    if test_val.is_integer():
        int_val = int(test_val)
        if min_float <= int_val <= max_float:
            result = checker(int_val)
            assert result == int_val
        else:
            with pytest.raises(ValueError):
                checker(int_val)


# Test edge case: boolean with numeric strings
@given(st.text(alphabet="01", min_size=1, max_size=10))
def test_boolean_numeric_strings(text):
    """Test boolean with strings that look numeric"""
    try:
        result = validators.boolean(text)
        # Should only work for "0" or "1", not "00", "01", "10", etc
        assert text in ["0", "1"]
        assert result == (text == "1")
    except ValueError:
        assert text not in ["0", "1"]


# Test edge case: Special numeric types
@given(st.one_of(
    st.decimals(allow_nan=False, allow_infinity=False),
    st.complex_numbers(allow_nan=False, allow_infinity=False)
))
def test_integer_special_numeric_types(value):
    """Test integer validator with Decimal and complex numbers"""
    # Decimal that represents an integer should work
    if isinstance(value, Decimal):
        try:
            if value == int(value):
                result = validators.integer(value)
                assert result == value
            else:
                with pytest.raises(ValueError):
                    validators.integer(value)
        except (ValueError, OverflowError):
            with pytest.raises(ValueError):
                validators.integer(value)
    
    # Complex numbers should fail
    if isinstance(value, complex):
        with pytest.raises((ValueError, TypeError)):
            validators.integer(value)


# Test edge case: Whitespace in string values
@given(
    value=st.integers(min_value=-100, max_value=100),
    prefix=st.text(alphabet=" \t\n", min_size=0, max_size=5),
    suffix=st.text(alphabet=" \t\n", min_size=0, max_size=5)
)
def test_integer_whitespace_handling(value, prefix, suffix):
    """Test integer validator with whitespace-padded strings"""
    padded = prefix + str(value) + suffix
    
    # Python's int() strips whitespace, so should work
    result = validators.integer(padded)
    assert result == padded  # Returns original with whitespace


# Test edge case: Boolean-like strings with different cases
@given(st.text(min_size=1, max_size=10))
def test_boolean_case_sensitivity(text):
    """Test boolean with various case combinations"""
    valid_true = ["True", "true", "1"]
    valid_false = ["False", "false", "0"]
    
    try:
        result = validators.boolean(text)
        assert text in valid_true + valid_false
        assert result == (text in valid_true)
    except ValueError:
        # Should fail for any other case variation
        assert text not in valid_true + valid_false
        # Check that case variations like "TRUE", "TrUe", etc fail
        if text.lower() in ["true", "false"] and text not in valid_true + valid_false:
            pass  # This is expected - case sensitive


# Test edge case: Byte strings
@given(st.binary(min_size=1, max_size=10))
def test_validators_with_bytes(byte_val):
    """Test validators with byte strings"""
    # Test integer validator with bytes
    try:
        # Try to decode as ASCII
        str_val = byte_val.decode('ascii')
        # If it's a valid integer string, integer validator might work
        try:
            int(str_val)
            result = validators.integer(byte_val)
            assert result == byte_val
        except ValueError:
            with pytest.raises(ValueError):
                validators.integer(byte_val)
    except UnicodeDecodeError:
        # Non-ASCII bytes should fail
        with pytest.raises((ValueError, TypeError)):
            validators.integer(byte_val)


# Test metamorphic property: chained integer_range validators
@given(
    min1=st.integers(min_value=-100, max_value=100),
    max1=st.integers(min_value=-100, max_value=100),
    min2=st.integers(min_value=-100, max_value=100),
    max2=st.integers(min_value=-100, max_value=100),
    value=st.integers(min_value=-200, max_value=200)
)
def test_integer_range_intersection(min1, max1, min2, max2, value):
    """Test that intersection of ranges works correctly"""
    assume(min1 <= max1 and min2 <= max2)
    
    checker1 = es_validators.integer_range(min1, max1)
    checker2 = es_validators.integer_range(min2, max2)
    
    # If value passes both checkers, it must be in intersection
    try:
        result1 = checker1(value)
        assert min1 <= value <= max1
        assert result1 == value
        
        try:
            result2 = checker2(value)
            assert min2 <= value <= max2
            assert result2 == value
            # Value is in intersection
            assert max(min1, min2) <= value <= min(max1, max2)
        except ValueError:
            # Value in range1 but not range2
            assert not (min2 <= value <= max2)
    except ValueError:
        # Value not in range1
        assert not (min1 <= value <= max1)


# Test snapshot hour with string inputs
@given(st.one_of(
    st.text(alphabet="0123456789-", min_size=1, max_size=3),
    st.integers(min_value=-50, max_value=50).map(str)
))
def test_snapshot_hour_string_inputs(hour_str):
    """Test snapshot hour validation with string inputs"""
    try:
        hour_int = int(hour_str)
        if 0 <= hour_int <= 23:
            result = es_validators.validate_automated_snapshot_start_hour(hour_str)
            assert result == hour_str  # Should return original string
        else:
            with pytest.raises(ValueError, match="Integer must be between 0 and 23"):
                es_validators.validate_automated_snapshot_start_hour(hour_str)
    except ValueError:
        # Invalid integer string
        with pytest.raises(ValueError):
            es_validators.validate_automated_snapshot_start_hour(hour_str)


# Test EBS validation with None properties
class MockEBSOptions:
    def __init__(self, properties):
        self.properties = properties

@given(st.dictionaries(
    keys=st.sampled_from(["VolumeType", "Iops", "VolumeSize", "EBSEnabled"]),
    values=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=10),
        st.integers()
    ),
    min_size=0,
    max_size=4
))
def test_ebs_options_with_various_properties(properties):
    """Test EBS options validation with various property combinations"""
    mock_obj = MockEBSOptions(properties)
    
    volume_type = properties.get("VolumeType")
    iops = properties.get("Iops")
    
    # Only constraint: io1 requires Iops
    if volume_type == "io1" and not iops:
        with pytest.raises(ValueError, match="Must specify Iops if VolumeType is 'io1'"):
            es_validators.validate_ebs_options(mock_obj)
    else:
        # Should not raise for any other combination
        result = es_validators.validate_ebs_options(mock_obj)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])