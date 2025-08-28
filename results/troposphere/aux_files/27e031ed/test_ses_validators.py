"""Property-based tests for troposphere.ses validators"""

import math
from hypothesis import given, strategies as st, assume
import troposphere.ses as ses


# Boolean validator tests

@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(["0", "1", "true", "True", "false", "False"])
))
def test_boolean_idempotence(x):
    """Test that boolean(boolean(x)) == boolean(x) for valid inputs"""
    try:
        result1 = ses.boolean(x)
        result2 = ses.boolean(result1)
        assert result1 == result2
    except ValueError:
        # If the input is invalid, that's fine
        pass


@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(["0", "1", "true", "True", "false", "False"])
))
def test_boolean_type_preservation(x):
    """Test that boolean always returns a Python bool"""
    try:
        result = ses.boolean(x)
        assert isinstance(result, bool)
        assert result in [True, False]
    except ValueError:
        # If the input is invalid, that's fine
        pass


@given(st.text())
def test_boolean_invalid_strings(s):
    """Test that invalid strings raise ValueError"""
    if s not in ["0", "1", "true", "True", "false", "False"]:
        try:
            ses.boolean(s)
            assert False, f"Should have raised ValueError for {s!r}"
        except ValueError:
            pass  # Expected


# Double validator tests

@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.-+eE", min_size=1).filter(
        lambda x: x not in [".", "-", "+", "e", "E", "--", "++", ".-", ".+"]
    )
))
def test_double_idempotence(x):
    """Test that double(double(x)) == double(x) for valid inputs"""
    try:
        result1 = ses.double(x)
        result2 = ses.double(result1)
        assert result1 == result2
    except ValueError:
        # If the input is invalid, that's fine
        pass


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.-+eE", min_size=1)
))
def test_double_float_convertible(x):
    """Test that valid doubles can be converted to float"""
    try:
        result = ses.double(x)
        # If double returns successfully, float() should work
        float_val = float(result)
        assert isinstance(float_val, float)
    except ValueError:
        # If the input is invalid, that's fine
        pass


@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.text()
))
def test_double_preserves_nan_infinity(x):
    """Test how double handles NaN and infinity"""
    try:
        result = ses.double(x)
        float_val = float(result)
        # Check that special values are preserved
        if isinstance(x, float):
            if math.isnan(x):
                assert math.isnan(float_val)
            elif math.isinf(x):
                assert math.isinf(float_val)
    except (ValueError, TypeError):
        # Expected for invalid inputs
        pass


# Cross-validator consistency tests

@given(st.sampled_from([True, False, 1, 0]))
def test_boolean_double_consistency(x):
    """Test that boolean and double validators handle overlapping values consistently"""
    # Both validators should accept 0 and 1
    if x in [0, 1]:
        bool_result = ses.boolean(x)
        double_result = ses.double(x)
        
        # Check that the numeric value is preserved
        assert float(double_result) == float(x)
        assert bool_result == bool(x)