"""Property-based tests for troposphere.scheduler module"""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest

from troposphere.validators import boolean, double
from troposphere.validators.scheduler import (
    validate_flexibletimewindow_mode,
    validate_ecsparameters_tags,
)


# Test validate_flexibletimewindow_mode
@given(st.text())
def test_flexibletimewindow_mode_invalid_strings(mode):
    """Any string not in ["OFF", "FLEXIBLE"] should raise ValueError"""
    assume(mode not in ["OFF", "FLEXIBLE"])
    with pytest.raises(ValueError, match="is not a valid mode"):
        validate_flexibletimewindow_mode(mode)


@given(st.sampled_from(["OFF", "FLEXIBLE"]))
def test_flexibletimewindow_mode_valid(mode):
    """Valid modes should return unchanged"""
    assert validate_flexibletimewindow_mode(mode) == mode


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.none(),
    st.booleans()
))
def test_flexibletimewindow_mode_non_string_types(mode):
    """Non-string types should raise ValueError if not in valid modes"""
    if mode not in ["OFF", "FLEXIBLE"]:
        with pytest.raises(ValueError, match="is not a valid mode"):
            validate_flexibletimewindow_mode(mode)


# Test validate_ecsparameters_tags
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.booleans(),
    st.just(""),
    st.just(0),
    st.just(False)
))
def test_ecsparameters_tags_non_none(tags):
    """Any non-None value should raise ValueError"""
    with pytest.raises(ValueError, match="EcsParameters Tags must be None"):
        validate_ecsparameters_tags(tags)


@given(st.none())
def test_ecsparameters_tags_none(tags):
    """None should return None"""
    assert validate_ecsparameters_tags(tags) is None


# Test boolean validator
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_values(value):
    """Values that should map to True"""
    assert boolean(value) is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_false_values(value):
    """Values that should map to False"""
    assert boolean(value) is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(allow_nan=False).filter(lambda x: x not in [0.0, 1.0]),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.none()
))
def test_boolean_invalid_values(value):
    """Invalid values should raise ValueError"""
    with pytest.raises(ValueError):
        boolean(value)


# Test double validator
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_valid_floats(value):
    """Valid floats should return unchanged"""
    result = double(value)
    assert result == value
    assert float(result) == float(value)


@given(st.integers())
def test_double_valid_integers(value):
    """Integers should be accepted as doubles"""
    result = double(value)
    assert result == value
    assert float(result) == float(value)


@given(st.text(min_size=1).map(str))
def test_double_string_numbers(value):
    """String representations of numbers"""
    try:
        expected = float(value)
        result = double(value)
        assert result == value
        assert float(result) == expected
    except (ValueError, TypeError):
        # If float() fails, double() should also fail
        with pytest.raises(ValueError, match="is not a valid double"):
            double(value)


@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.text().filter(lambda x: x not in ["inf", "-inf", "nan"])  # Special float strings
))
def test_double_invalid_types(value):
    """Types that can't be converted to float should raise ValueError"""
    try:
        float(value)
    except (ValueError, TypeError):
        with pytest.raises(ValueError, match="is not a valid double"):
            double(value)


# Property: boolean function should be deterministic
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"])
))
def test_boolean_deterministic(value):
    """boolean function should always return the same result for the same input"""
    result1 = boolean(value)
    result2 = boolean(value)
    assert result1 == result2


# Property: double function preserves numeric value
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers()
))
def test_double_preserves_numeric_value(value):
    """double function should preserve the numeric value"""
    result = double(value)
    assert float(result) == float(value)


# Edge case: boolean with float values 0.0 and 1.0
@given(st.sampled_from([0.0, 1.0]))
def test_boolean_float_edge_cases(value):
    """Test boolean with float 0.0 and 1.0"""
    # Based on the implementation, 0.0 should map to False and 1.0 to True
    # since they compare equal to 0 and 1
    if value == 0.0:
        assert boolean(value) is False
    elif value == 1.0:
        assert boolean(value) is True


# Test case sensitivity in flexibletimewindow_mode
@given(st.sampled_from(["off", "Off", "flexible", "Flexible", "FLEXIBLE ", " OFF"]))
def test_flexibletimewindow_mode_case_sensitivity(mode):
    """Test that mode validation is case-sensitive"""
    if mode not in ["OFF", "FLEXIBLE"]:
        with pytest.raises(ValueError, match="is not a valid mode"):
            validate_flexibletimewindow_mode(mode)