import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the validators we're testing
from troposphere.validators import boolean, integer
from troposphere.validators.dlm import (
    validate_interval,
    validate_interval_unit,
    validate_state,
)


# Test boolean validator
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True")
))
def test_boolean_returns_true_for_truthy_values(value):
    """Boolean validator should return True for documented truthy values"""
    assert boolean(value) is True


@given(st.one_of(
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_returns_false_for_falsy_values(value):
    """Boolean validator should return False for documented falsy values"""
    assert boolean(value) is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none(),
))
def test_boolean_raises_for_invalid_values(value):
    """Boolean validator should raise ValueError for non-boolean-like values"""
    with pytest.raises(ValueError):
        boolean(value)


# Test integer validator
@given(st.integers())
def test_integer_accepts_integers(value):
    """Integer validator should accept actual integers and return them unchanged"""
    result = integer(value)
    assert result == value
    assert int(result) == value


@given(st.text(min_size=1).map(str))
def test_integer_accepts_string_integers(value):
    """Integer validator should accept string representations of integers"""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(value)


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer()),
    st.text().filter(lambda x: not x.isdigit() and not (x.startswith('-') and x[1:].isdigit())),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none(),
))  
def test_integer_raises_for_non_integers(value):
    """Integer validator should raise ValueError for non-integer values"""
    # Skip values that can actually be converted to int
    try:
        int(value)
        assume(False)  # Skip if it can be converted
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(value)


# Test validate_interval
@given(st.sampled_from([1, 2, 3, 4, 6, 8, 12, 24]))
def test_validate_interval_accepts_valid_intervals(value):
    """validate_interval should accept documented valid intervals"""
    assert validate_interval(value) == value


@given(st.integers().filter(lambda x: x not in [1, 2, 3, 4, 6, 8, 12, 24]))
def test_validate_interval_rejects_invalid_intervals(value):
    """validate_interval should reject intervals not in the valid set"""
    with pytest.raises(ValueError, match="Interval must be one of"):
        validate_interval(value)


@given(st.one_of(
    st.floats(),
    st.text(),
    st.lists(st.integers()),
    st.none(),
))
def test_validate_interval_handles_non_integers(value):
    """validate_interval behavior with non-integer inputs"""
    # The function doesn't explicitly check type, it just checks membership
    # So anything not in the valid set should raise ValueError
    with pytest.raises(ValueError, match="Interval must be one of"):
        validate_interval(value)


# Test validate_interval_unit  
@given(st.just("HOURS"))
def test_validate_interval_unit_accepts_hours(value):
    """validate_interval_unit should accept 'HOURS'"""
    assert validate_interval_unit(value) == "HOURS"


@given(st.text().filter(lambda x: x != "HOURS"))
def test_validate_interval_unit_rejects_non_hours(value):
    """validate_interval_unit should reject anything except 'HOURS'"""
    with pytest.raises(ValueError, match="Interval unit must be one of"):
        validate_interval_unit(value)


@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.none(),
))
def test_validate_interval_unit_handles_non_strings(value):
    """validate_interval_unit behavior with non-string inputs"""
    with pytest.raises(ValueError, match="Interval unit must be one of"):
        validate_interval_unit(value)


# Test validate_state
@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_validate_state_accepts_valid_states(value):
    """validate_state should accept 'ENABLED' or 'DISABLED'"""
    assert validate_state(value) == value


@given(st.text().filter(lambda x: x not in ["ENABLED", "DISABLED"]))
def test_validate_state_rejects_invalid_states(value):
    """validate_state should reject states not in the valid set"""
    with pytest.raises(ValueError, match="State must be one of"):
        validate_state(value)


@given(st.one_of(
    st.integers(),
    st.floats(), 
    st.lists(st.text()),
    st.none(),
))
def test_validate_state_handles_non_strings(value):
    """validate_state behavior with non-string inputs"""
    with pytest.raises(ValueError, match="State must be one of"):
        validate_state(value)


# Edge case tests for boolean validator
def test_boolean_string_with_spaces():
    """Test boolean validator with strings containing spaces"""
    with pytest.raises(ValueError):
        boolean(" true")
    with pytest.raises(ValueError):
        boolean("true ")
    with pytest.raises(ValueError):
        boolean(" false ")


def test_boolean_case_sensitivity():
    """Test boolean validator case sensitivity"""
    # These should work according to the code
    assert boolean("True") is True
    assert boolean("true") is True
    assert boolean("False") is False
    assert boolean("false") is False
    
    # These should not work
    with pytest.raises(ValueError):
        boolean("TRUE")
    with pytest.raises(ValueError):
        boolean("FALSE")
    with pytest.raises(ValueError):
        boolean("tRue")
    with pytest.raises(ValueError):
        boolean("fAlse")


# Edge case for integer validator
def test_integer_preserves_type():
    """Integer validator should preserve the original type, not convert"""
    # String stays string
    result = integer("42")
    assert result == "42"
    assert isinstance(result, str)
    
    # Int stays int
    result = integer(42)
    assert result == 42
    assert isinstance(result, int)


def test_integer_with_leading_zeros():
    """Test integer validator with leading zeros in strings"""
    # Python's int() handles leading zeros
    result = integer("007")
    assert result == "007"
    assert int(result) == 7


def test_integer_with_negative():
    """Test integer validator with negative numbers"""
    result = integer(-42)
    assert result == -42
    
    result = integer("-42")
    assert result == "-42"
    assert int(result) == -42


# Edge cases for interval validation
def test_validate_interval_boundary_values():
    """Test validate_interval with boundary values"""
    # Just before and after valid values
    with pytest.raises(ValueError):
        validate_interval(0)
    assert validate_interval(1) == 1
    assert validate_interval(2) == 2
    with pytest.raises(ValueError):
        validate_interval(5)
    assert validate_interval(6) == 6
    with pytest.raises(ValueError):
        validate_interval(7)
    assert validate_interval(8) == 8
    with pytest.raises(ValueError):
        validate_interval(25)
    assert validate_interval(24) == 24


# Test for potential issues with boolean("1") vs boolean(1)
@given(st.sampled_from([1, "1"]))
def test_boolean_one_representations(value):
    """Both integer 1 and string '1' should return True"""
    assert boolean(value) is True


@given(st.sampled_from([0, "0"]))
def test_boolean_zero_representations(value):
    """Both integer 0 and string '0' should return False"""
    assert boolean(value) is False