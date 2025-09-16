import troposphere.pipes
from hypothesis import given, strategies as st, assume
import pytest


# Test the boolean function
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_idempotence(x):
    """boolean(boolean(x)) should equal boolean(x) for valid inputs"""
    result = troposphere.pipes.boolean(x)
    double_result = troposphere.pipes.boolean(result)
    assert result == double_result


@given(st.one_of(st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True")))
def test_boolean_true_values(x):
    """Values that should map to True"""
    assert troposphere.pipes.boolean(x) is True


@given(st.one_of(st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")))
def test_boolean_false_values(x):
    """Values that should map to False"""
    assert troposphere.pipes.boolean(x) is False


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_values_raise(x):
    """Non-accepted values should raise ValueError"""
    with pytest.raises(ValueError):
        troposphere.pipes.boolean(x)


# Test the integer function
@given(st.integers())
def test_integer_preserves_valid_integers(x):
    """integer(x) should return x unchanged for valid integers"""
    result = troposphere.pipes.integer(x)
    assert result == x
    assert int(result) == x


@given(st.text(min_size=1).map(str))
def test_integer_preserves_valid_string_integers(x):
    """integer(x) should preserve string representations of integers"""
    try:
        int(x)
    except (ValueError, TypeError):
        assume(False)  # Skip non-integer strings
    
    result = troposphere.pipes.integer(x)
    assert result == x
    assert int(result) == int(x)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans()
))
def test_integer_handles_convertible_types(x):
    """integer(x) should work for types convertible to int"""
    try:
        expected = int(x)
    except (ValueError, TypeError):
        assume(False)
    
    result = troposphere.pipes.integer(x)
    assert result == x
    assert int(result) == expected


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: not x.isdigit() and not (x.startswith('-') and x[1:].isdigit())),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.just(None),
    st.floats(allow_nan=True),
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_integer_invalid_values_raise_with_message(x):
    """Invalid values should raise ValueError with specific message format"""
    with pytest.raises(ValueError) as excinfo:
        troposphere.pipes.integer(x)
    assert "%r is not a valid integer" % x in str(excinfo.value)


# Edge case tests
@given(st.text())
def test_boolean_case_sensitivity(s):
    """Test case sensitivity of boolean string conversion"""
    if s.lower() == "true":
        if s in ["true", "True"]:
            assert troposphere.pipes.boolean(s) is True
        else:
            with pytest.raises(ValueError):
                troposphere.pipes.boolean(s)
    elif s.lower() == "false":
        if s in ["false", "False"]:
            assert troposphere.pipes.boolean(s) is False
        else:
            with pytest.raises(ValueError):
                troposphere.pipes.boolean(s)


@given(st.floats())
def test_integer_float_handling(x):
    """Test how integer function handles float values"""
    if x != x:  # NaN check
        with pytest.raises(ValueError) as excinfo:
            troposphere.pipes.integer(x)
        assert "%r is not a valid integer" % x in str(excinfo.value)
    elif x in [float('inf'), float('-inf')]:
        with pytest.raises(ValueError) as excinfo:
            troposphere.pipes.integer(x)
        assert "%r is not a valid integer" % x in str(excinfo.value)
    else:
        # Regular floats should pass validation but preserve original value
        result = troposphere.pipes.integer(x)
        assert result == x
        # Should be convertible to int (though may lose precision)
        int(result)