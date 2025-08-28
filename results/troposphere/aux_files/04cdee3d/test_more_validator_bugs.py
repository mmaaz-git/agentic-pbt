"""Test for more potential bugs in troposphere validators."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere import validators
import math


# Test positive_integer validator
@given(st.one_of(
    st.floats(),
    st.integers(),
    st.text()
))
def test_positive_integer_validator(value):
    """Test positive_integer validator for consistency."""
    
    # First check if it's a valid integer
    try:
        validators.integer(value)
        is_valid_integer = True
    except (ValueError, OverflowError):  # We know about the OverflowError bug
        is_valid_integer = False
    
    if not is_valid_integer:
        # If not a valid integer, positive_integer should also fail
        with pytest.raises((ValueError, OverflowError)):
            validators.positive_integer(value)
    else:
        # If it's a valid integer, check if it's positive
        try:
            int_val = int(value)
            if int_val >= 0:
                result = validators.positive_integer(value)
                assert result == value
            else:
                with pytest.raises(ValueError):
                    validators.positive_integer(value)
        except (ValueError, TypeError, OverflowError):
            with pytest.raises((ValueError, OverflowError)):
                validators.positive_integer(value)


# Test integer_range validator
@given(
    value=st.one_of(st.integers(), st.floats()),
    min_val=st.integers(min_value=-1000, max_value=1000),
    max_val=st.integers(min_value=-1000, max_value=1000)
)
def test_integer_range_validator(value, min_val, max_val):
    """Test integer_range validator."""
    
    # Only test valid ranges
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    validator = validators.integer_range(min_val, max_val)
    
    try:
        int_val = int(value)
        if min_val <= int_val <= max_val:
            result = validator(value)
            assert result == value
        else:
            with pytest.raises(ValueError):
                validator(value)
    except (ValueError, TypeError, OverflowError):
        with pytest.raises((ValueError, TypeError, OverflowError)):
            validator(value)


# Test network_port edge cases with special values
def test_network_port_special_values():
    """Test network_port validator with edge case values."""
    
    # Test boundary values
    assert validators.network_port(-1) == -1
    assert validators.network_port(0) == 0
    assert validators.network_port(65535) == 65535
    
    # These should fail
    with pytest.raises(ValueError):
        validators.network_port(-2)
    
    with pytest.raises(ValueError):
        validators.network_port(65536)
    
    # Test with string representations
    assert validators.network_port("-1") == "-1"
    assert validators.network_port("0") == "0"
    assert validators.network_port("65535") == "65535"
    
    # Test with float representations
    assert validators.network_port(-1.0) == -1.0
    assert validators.network_port(0.0) == 0.0
    assert validators.network_port(65535.0) == 65535.0
    
    # Float with fractional part should work if convertible to int
    assert validators.network_port(80.0) == 80.0
    
    # But non-integer floats should fail
    with pytest.raises(ValueError):
        validators.network_port(80.5)


# Test s3_bucket_name with edge cases
def test_s3_bucket_name_edge_cases():
    """Test s3_bucket_name validator edge cases."""
    
    # Minimum length bucket name (3 chars)
    assert validators.s3_bucket_name("abc") == "abc"
    assert validators.s3_bucket_name("a1b") == "a1b"
    
    # Maximum length bucket name (63 chars)
    long_name = "a" + "b" * 61 + "c"
    assert len(long_name) == 63
    assert validators.s3_bucket_name(long_name) == long_name
    
    # Too short (less than 3 chars)
    with pytest.raises(ValueError):
        validators.s3_bucket_name("ab")
    
    # Too long (more than 63 chars)
    with pytest.raises(ValueError):
        validators.s3_bucket_name("a" * 64)
    
    # Starting with period
    with pytest.raises(ValueError):
        validators.s3_bucket_name(".bucket")
    
    # Ending with period
    with pytest.raises(ValueError):
        validators.s3_bucket_name("bucket.")
    
    # Starting with hyphen
    with pytest.raises(ValueError):
        validators.s3_bucket_name("-bucket")
    
    # Ending with hyphen
    with pytest.raises(ValueError):
        validators.s3_bucket_name("bucket-")
    
    # Consecutive periods
    with pytest.raises(ValueError):
        validators.s3_bucket_name("bucket..name")
    
    # IP address format
    with pytest.raises(ValueError):
        validators.s3_bucket_name("192.168.1.1")
    
    # Valid names with periods and hyphens
    assert validators.s3_bucket_name("my-bucket") == "my-bucket"
    assert validators.s3_bucket_name("my.bucket") == "my.bucket"
    assert validators.s3_bucket_name("my-bucket.name") == "my-bucket.name"
    
    # Uppercase letters not allowed
    with pytest.raises(ValueError):
        validators.s3_bucket_name("MyBucket")
    
    # Special characters not allowed
    with pytest.raises(ValueError):
        validators.s3_bucket_name("my_bucket")
    
    with pytest.raises(ValueError):
        validators.s3_bucket_name("my@bucket")


# Test boolean edge case with "1" and 1 strings 
def test_boolean_string_number_edge_cases():
    """Test boolean validator with string number edge cases."""
    
    # These should return True
    assert validators.boolean("1") is True
    assert validators.boolean(1) is True
    assert validators.boolean(True) is True
    
    # These should return False  
    assert validators.boolean("0") is False
    assert validators.boolean(0) is False
    assert validators.boolean(False) is False
    
    # But what about "01" or "00"?
    with pytest.raises(ValueError):
        validators.boolean("01")
    
    with pytest.raises(ValueError):
        validators.boolean("00")
    
    # What about 1.0 and 0.0?
    with pytest.raises(ValueError):
        validators.boolean(1.0)
    
    with pytest.raises(ValueError):
        validators.boolean(0.0)
    
    # What about whitespace?
    with pytest.raises(ValueError):
        validators.boolean(" true ")
    
    with pytest.raises(ValueError):
        validators.boolean("true ")
    
    with pytest.raises(ValueError):
        validators.boolean(" true")


# Test json_checker edge cases
def test_json_checker_edge_cases():
    """Test json_checker validator edge cases."""
    
    # Valid JSON string
    assert validators.json_checker('{"key": "value"}') == '{"key": "value"}'
    
    # Valid dict (should be converted to JSON string)
    result = validators.json_checker({"key": "value"})
    import json
    assert json.loads(result) == {"key": "value"}
    
    # Empty dict
    result = validators.json_checker({})
    assert result == "{}"
    
    # Empty JSON string
    assert validators.json_checker("{}") == "{}"
    
    # Invalid JSON string should raise
    with pytest.raises(json.JSONDecodeError):
        validators.json_checker("{invalid json}")
    
    # Non-string, non-dict should raise TypeError
    with pytest.raises(TypeError):
        validators.json_checker(123)
    
    with pytest.raises(TypeError):
        validators.json_checker([1, 2, 3])
    
    # Nested structures
    nested = {"a": {"b": {"c": "d"}}}
    result = validators.json_checker(nested)
    assert json.loads(result) == nested
    
    # Arrays in JSON
    assert validators.json_checker('[]') == '[]'
    assert validators.json_checker('[1, 2, 3]') == '[1, 2, 3]'


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])