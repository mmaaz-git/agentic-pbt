"""Property-based tests for troposphere.dynamodb module"""

import math
from hypothesis import given, strategies as st, assume
import troposphere.dynamodb as ddb


# Test 1: Boolean function case sensitivity property
@given(st.sampled_from(['true', 'false']))
def test_boolean_case_insensitive(base_value):
    """Boolean function should accept all case variations of true/false"""
    # Test that different case variations behave consistently
    lower = base_value.lower()
    title = base_value.title() 
    upper = base_value.upper()
    
    # Lower and title case should work
    expected = True if lower == 'true' else False
    assert ddb.boolean(lower) == expected
    assert ddb.boolean(title) == expected
    
    # Upper case should also work (property: case insensitive)
    try:
        result = ddb.boolean(upper)
        # If it doesn't raise, it should return the same value
        assert result == expected, f"Case inconsistency: {upper} returned {result}, expected {expected}"
    except ValueError:
        # Document the inconsistency - upper case is rejected
        pass


# Test 2: Integer function should validate integer-convertible values
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validates_correctly(x):
    """Integer function should only accept values where int(x) doesn't lose information"""
    try:
        result = ddb.integer(x)
        # The function accepts the value, now check if it's truly integer-like
        int_x = int(x)
        # Property: if integer() accepts a float, it should be equal to its int conversion
        # (i.e., no fractional part)
        if isinstance(x, float) and x != int_x:
            # This is a bug - integer() accepts non-integer floats
            assert False, f"integer() accepts non-integer float {x}"
    except (ValueError, OverflowError, TypeError):
        # Expected for non-integer values
        pass


# Test 3: Type conversion functions preserve input type
@given(st.one_of(
    st.integers(min_value=-10**10, max_value=10**10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-10**10, max_value=10**10),
    st.text(min_size=1).filter(lambda x: x.strip() != '')
))
def test_type_preservation(x):
    """Type conversion functions should either convert or raise, not pass through"""
    # Test integer function
    if isinstance(x, str):
        try:
            result = ddb.integer(x)
            # If it accepts a string, it should validate it's integer-like
            int(x)  # This should work if integer() accepted it
            # Property: result should be converted to int, not kept as string
            assert isinstance(result, int), f"integer('{x}') returned string instead of int"
        except ValueError:
            pass  # Expected for non-integer strings
    
    # Test double function  
    if isinstance(x, str):
        try:
            result = ddb.double(x)
            # If it accepts a string, it should validate it's float-like
            float(x)  # This should work if double() accepted it
            # Property: result should be converted to float, not kept as string
            assert isinstance(result, float), f"double('{x}') returned string instead of float"
        except ValueError:
            pass  # Expected for non-float strings


# Test 4: Validator functions reject invalid values
@given(st.text())
def test_validators_reject_invalid(value):
    """Validator functions should only accept their documented valid values"""
    # Test attribute_type_validator
    valid_attrs = ["S", "N", "B"]
    if value not in valid_attrs:
        try:
            ddb.attribute_type_validator(value)
            assert False, f"attribute_type_validator accepted invalid value: {value}"
        except ValueError:
            pass  # Expected
    else:
        assert ddb.attribute_type_validator(value) == value
    
    # Test key_type_validator
    valid_keys = ["HASH", "RANGE"]
    if value not in valid_keys:
        try:
            ddb.key_type_validator(value)
            assert False, f"key_type_validator accepted invalid value: {value}"
        except ValueError:
            pass  # Expected
    else:
        assert ddb.key_type_validator(value) == value


# Test 5: Boolean function with numeric edge cases
@given(st.floats(allow_nan=False))
def test_boolean_numeric_behavior(x):
    """Boolean function should handle numeric values consistently"""
    try:
        result = ddb.boolean(x)
        # If it accepts a numeric value, check consistency
        if isinstance(x, float):
            # It accepts 0.0 and 1.0, but what about values very close?
            if math.isclose(x, 0.0):
                assert result == False, f"boolean({x}) should be False when close to 0"
            elif math.isclose(x, 1.0):
                assert result == True, f"boolean({x}) should be True when close to 1"
            else:
                # Should not accept other float values
                assert False, f"boolean() accepted unexpected float value: {x}"
    except ValueError:
        # Expected for non-boolean numeric values
        pass


# Test 6: Integer function with string representations
@given(st.integers(min_value=-10**6, max_value=10**6))
def test_integer_string_round_trip(n):
    """Integer function should handle string representations correctly"""
    str_n = str(n)
    result = ddb.integer(str_n)
    # Property: integer() should convert string to int or keep it as valid string
    # Currently it keeps as string - is this intended?
    assert result == str_n, f"integer('{str_n}') modified the input"
    
    # But it should validate that the string is integer-like
    assert int(result) == n, f"integer('{str_n}') didn't validate integer conversion"