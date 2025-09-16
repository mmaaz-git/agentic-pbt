"""Property-based tests for troposphere.wisdom module."""

import math
from hypothesis import given, strategies as st, assume
import troposphere.wisdom as wisdom


# Strategy for values that should be valid doubles
valid_doubles = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text().filter(lambda s: s.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).isdigit()),
    st.booleans(),
)

# Strategy for complex numeric strings
numeric_strings = st.one_of(
    st.from_regex(r'^[+-]?\d+$', fullmatch=True),  # integers as strings
    st.from_regex(r'^[+-]?\d+\.\d+$', fullmatch=True),  # floats as strings
    st.from_regex(r'^[+-]?\d+\.?$', fullmatch=True),  # trailing dot
    st.from_regex(r'^[+-]?\.\d+$', fullmatch=True),  # leading dot
    st.from_regex(r'^[+-]?\d+[eE][+-]?\d+$', fullmatch=True),  # scientific notation
    st.from_regex(r'^[+-]?\d+\.\d+[eE][+-]?\d+$', fullmatch=True),  # scientific with decimal
)

# Strategy for any input that float() accepts
floatable_values = st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    numeric_strings,
    st.booleans(),
    st.just(bytearray(b'123')),
    st.just(b'456'),
)


@given(floatable_values)
def test_identity_property(x):
    """Test that double(x) returns x unchanged for valid inputs."""
    try:
        result = wisdom.double(x)
        assert result is x, f"double({x!r}) returned {result!r}, expected same object"
    except ValueError:
        # If double raises ValueError, float should also raise an exception
        try:
            float(x)
            assert False, f"double({x!r}) raised ValueError but float({x!r}) succeeded"
        except (ValueError, TypeError):
            pass  # Expected


@given(floatable_values)
def test_idempotence(x):
    """Test that double(double(x)) == double(x) for valid inputs."""
    try:
        result1 = wisdom.double(x)
        result2 = wisdom.double(result1)
        assert result2 is result1, f"double is not idempotent for {x!r}"
    except ValueError:
        pass  # Invalid input, skip


@given(floatable_values)
def test_float_compatibility(x):
    """Test that if float(x) succeeds, double(x) should also succeed."""
    try:
        float_result = float(x)
        # float() succeeded, so double() should also succeed
        try:
            double_result = wisdom.double(x)
            # Both succeeded - good
        except ValueError as e:
            assert False, f"float({x!r}) succeeded but double({x!r}) raised: {e}"
    except (ValueError, TypeError):
        # float() failed, so double() should also fail
        try:
            wisdom.double(x)
            assert False, f"float({x!r}) failed but double({x!r}) succeeded"
        except ValueError:
            pass  # Expected


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.binary(),
    st.just(bytearray(b'123'))
))
def test_type_preservation(x):
    """Test that the output type matches the input type for valid inputs."""
    try:
        result = wisdom.double(x)
        assert type(result) == type(x), f"Type not preserved: {type(x).__name__} -> {type(result).__name__}"
    except ValueError:
        pass  # Invalid input, skip


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
))
def test_error_message_format(x):
    """Test that invalid inputs produce correctly formatted error messages."""
    try:
        wisdom.double(x)
        # If we get here, check that float() also succeeds
        try:
            float(x)
        except (ValueError, TypeError):
            assert False, f"double({x!r}) succeeded but float({x!r}) failed"
    except ValueError as e:
        expected_msg = f"{x!r} is not a valid double"
        assert str(e) == expected_msg, f"Error message mismatch: got {str(e)!r}, expected {expected_msg!r}"


# Additional edge cases
@given(st.text())
def test_string_handling(s):
    """Test string handling matches float() behavior."""
    float_succeeded = False
    float_error = None
    try:
        float(s)
        float_succeeded = True
    except (ValueError, TypeError) as e:
        float_error = e
    
    double_succeeded = False
    double_error = None
    try:
        wisdom.double(s)
        double_succeeded = True
    except ValueError as e:
        double_error = e
    
    if float_succeeded:
        assert double_succeeded, f"float({s!r}) succeeded but double({s!r}) failed: {double_error}"
    else:
        assert not double_succeeded, f"float({s!r}) failed but double({s!r}) succeeded"


@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.just('inf'),
    st.just('-inf'),
    st.just('nan'),
    st.just('Infinity'),
    st.just('-Infinity'),
    st.just('NaN'),
))
def test_special_float_values(x):
    """Test handling of special float values (inf, -inf, nan)."""
    # These should all be accepted by float()
    float_val = float(x) if isinstance(x, str) else x
    
    # double() should also accept them
    result = wisdom.double(x)
    assert result is x, f"double({x!r}) should return the input unchanged"


# Test with actual CloudFormation usage
@given(st.one_of(
    st.integers(min_value=0, max_value=10000),
    st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    st.from_regex(r'^\d+(\.\d+)?$', fullmatch=True).filter(lambda s: float(s) <= 10000),
))
def test_semantic_chunking_config_property(value):
    """Test that double validator works correctly in actual CloudFormation class."""
    config = wisdom.SemanticChunkingConfiguration()
    
    # This should not raise an error
    config.MaxTokens = value
    
    # The value should be stored as-is
    assert config.MaxTokens is value
    
    # Should be able to convert to dict
    result = config.to_dict()
    assert 'MaxTokens' in result
    assert result['MaxTokens'] is value