"""Property-based tests for troposphere.eks module"""

import troposphere.eks as eks
from hypothesis import given, strategies as st, assume
import pytest


# Test that validate_taint_key handles all input types properly
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.booleans(),
    st.binary(),
    st.complex_numbers(allow_nan=False, allow_infinity=False)
))
def test_validate_taint_key_non_string_types(value):
    """validate_taint_key should either:
    1. Accept the value and validate it properly 
    2. Raise a meaningful validation error
    
    It should NOT crash with TypeError about len()
    """
    try:
        result = eks.validate_taint_key(value)
        # If it succeeds, the result should be the same as input
        assert result == value
        # And it should pass length validation if it has a length
        if hasattr(value, '__len__'):
            assert 1 <= len(value) <= 63
    except ValueError as e:
        # ValueError is expected for invalid values
        assert "Taint Key" in str(e)
    except TypeError as e:
        # TypeError about len() indicates a bug - the validator doesn't check types
        if "has no len()" in str(e):
            pytest.fail(f"validate_taint_key crashed with TypeError on {type(value).__name__} input: {e}")
        else:
            # Other TypeErrors might be acceptable
            pass


# Test that validate_taint_value handles all input types properly  
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.booleans(),
    st.binary(),
    st.complex_numbers(allow_nan=False, allow_infinity=False)
))
def test_validate_taint_value_non_string_types(value):
    """validate_taint_value should either:
    1. Accept the value and validate it properly
    2. Raise a meaningful validation error
    
    It should NOT crash with TypeError about len()
    """
    try:
        result = eks.validate_taint_value(value)
        # If it succeeds, the result should be the same as input
        assert result == value
        # And it should pass length validation if it has a length
        if hasattr(value, '__len__'):
            assert len(value) <= 63
    except ValueError as e:
        # ValueError is expected for invalid values
        assert "Taint Value" in str(e)
    except TypeError as e:
        # TypeError about len() indicates a bug - the validator doesn't check types
        if "has no len()" in str(e):
            pytest.fail(f"validate_taint_value crashed with TypeError on {type(value).__name__} input: {e}")
        else:
            # Other TypeErrors might be acceptable
            pass


# Test string boundary conditions for validate_taint_key
@given(st.text())
def test_validate_taint_key_string_boundaries(s):
    """Test that validate_taint_key properly validates string length boundaries"""
    try:
        result = eks.validate_taint_key(s)
        # If validation passes, length should be in valid range
        assert 1 <= len(s) <= 63
        assert result == s
    except ValueError as e:
        # If validation fails, length should be outside valid range
        assert len(s) < 1 or len(s) > 63
        assert "Taint Key must be at least 1 character and maximum 63 characters" in str(e)


# Test string boundary conditions for validate_taint_value
@given(st.text())  
def test_validate_taint_value_string_boundaries(s):
    """Test that validate_taint_value properly validates string length boundaries"""
    try:
        result = eks.validate_taint_value(s)
        # If validation passes, length should be in valid range
        assert len(s) <= 63
        assert result == s
    except ValueError as e:
        # If validation fails, length should be outside valid range
        assert len(s) > 63
        assert "Taint Value maximum characters is 63" in str(e)


# Test that Taint class properly validates all field types
@given(
    key=st.one_of(
        st.text(),
        st.integers(),
        st.none(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ),
    value=st.one_of(
        st.text(),
        st.integers(),
        st.none(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ),
    effect=st.one_of(
        st.sampled_from(eks.VALID_TAINT_EFFECT),
        st.text(),
        st.integers(),
        st.none()
    )
)
def test_taint_class_type_validation(key, value, effect):
    """Taint class should properly validate all input types and not allow invalid objects"""
    try:
        taint = eks.Taint(Key=key, Value=value, Effect=effect)
        taint_dict = taint.to_dict()
        
        # If creation succeeds, all values should be valid
        # Key should be a string with 1-63 chars
        if not isinstance(key, str):
            pytest.fail(f"Taint accepted non-string Key: {type(key).__name__}")
        if not (1 <= len(key) <= 63):
            pytest.fail(f"Taint accepted invalid Key length: {len(key)}")
            
        # Value should be a string with 0-63 chars  
        if not isinstance(value, str):
            pytest.fail(f"Taint accepted non-string Value: {type(value).__name__}")
        if len(value) > 63:
            pytest.fail(f"Taint accepted invalid Value length: {len(value)}")
            
        # Effect should be one of the valid values
        if effect not in eks.VALID_TAINT_EFFECT:
            pytest.fail(f"Taint accepted invalid Effect: {effect}")
            
    except (ValueError, TypeError) as e:
        # Errors are expected for invalid inputs
        pass
    except Exception as e:
        # Unexpected error types might indicate a bug
        if "has no len()" in str(e):
            # This specific error indicates the validator bug
            pytest.fail(f"Taint validator crashed with TypeError: {e}")