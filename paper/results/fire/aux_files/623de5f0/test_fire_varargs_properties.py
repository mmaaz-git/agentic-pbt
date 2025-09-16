"""Property tests for varargs and kwargs components."""

import math
from hypothesis import given, strategies as st, assume
import fire.test_components as tc


@given(
    items=st.lists(
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)
        ),
        min_size=0,
        max_size=20
    )
)
def test_varargs_cumsums_length_property(items):
    """Test that cumsums returns list of same length as input."""
    va = tc.VarArgs()
    result = va.cumsums(*items)
    assert len(result) == len(items)


@given(
    items=st.lists(
        st.integers(min_value=-1000, max_value=1000),
        min_size=1,
        max_size=20
    )
)
def test_varargs_cumsums_cumulative_property(items):
    """Test that cumsums correctly computes cumulative sums."""
    va = tc.VarArgs()
    result = va.cumsums(*items)
    
    # Check each cumulative sum
    expected_sum = 0
    for i, item in enumerate(items):
        expected_sum += item
        assert result[i] == expected_sum


@given(
    items=st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
        min_size=1,
        max_size=20
    )
)
def test_varargs_cumsums_float_cumulative(items):
    """Test cumsums with floating point numbers."""
    va = tc.VarArgs()
    result = va.cumsums(*items)
    
    expected_sum = 0.0
    for i, item in enumerate(items):
        expected_sum += item
        assert math.isclose(result[i], expected_sum, rel_tol=1e-9)


def test_varargs_cumsums_empty():
    """Test that cumsums with no arguments returns empty list."""
    va = tc.VarArgs()
    result = va.cumsums()
    assert result == []


@given(
    first=st.text(min_size=1, max_size=10)
)
def test_varargs_cumsums_single_string(first):
    """Test cumsums with single string input."""
    va = tc.VarArgs()
    result = va.cumsums(first)
    assert result == [first]


@given(
    strings=st.lists(
        st.text(min_size=1, max_size=5),
        min_size=2,
        max_size=10
    )
)
def test_varargs_cumsums_string_concatenation(strings):
    """Test that cumsums concatenates strings."""
    va = tc.VarArgs()
    result = va.cumsums(*strings)
    
    expected = []
    accumulated = ""
    for s in strings:
        if accumulated == "":
            accumulated = s
        else:
            accumulated = accumulated + s
        expected.append(accumulated)
    
    assert result == expected


@given(
    lists=st.lists(
        st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=3),
        min_size=2,
        max_size=5
    )
)
def test_varargs_cumsums_list_concatenation(lists):
    """Test that cumsums concatenates lists."""
    va = tc.VarArgs()
    result = va.cumsums(*lists)
    
    expected = []
    accumulated = None
    for lst in lists:
        if accumulated is None:
            accumulated = lst
        else:
            accumulated = accumulated + lst
        expected.append(accumulated)
    
    assert result == expected


@given(
    alpha=st.integers(min_value=-100, max_value=100),
    beta=st.integers(min_value=-100, max_value=100),
    chars=st.lists(st.text(min_size=1, max_size=1), max_size=10)
)
def test_varargs_varchars(alpha, beta, chars):
    """Test VarArgs.varchars returns correct tuple."""
    va = tc.VarArgs()
    result = va.varchars(alpha, beta, *chars)
    
    assert result[0] == alpha
    assert result[1] == beta
    assert result[2] == ''.join(chars)


def test_varargs_varchars_defaults():
    """Test VarArgs.varchars with default values."""
    va = tc.VarArgs()
    result = va.varchars()
    assert result == (0, 0, '')


@given(
    kwargs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=0,
        max_size=5
    )
)
def test_kwargs_props_identity(kwargs):
    """Test that Kwargs.props returns the exact kwargs passed."""
    kw = tc.Kwargs()
    result = kw.props(**kwargs)
    assert result == kwargs


@given(
    kwargs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=1,
        max_size=5
    )
)
def test_kwargs_upper_sorted_keys(kwargs):
    """Test that Kwargs.upper returns sorted uppercase keys."""
    kw = tc.Kwargs()
    result = kw.upper(**kwargs)
    
    expected = ' '.join(sorted(kwargs.keys())).upper()
    assert result == expected


def test_kwargs_upper_empty():
    """Test Kwargs.upper with no arguments."""
    kw = tc.Kwargs()
    result = kw.upper()
    assert result == ''


@given(
    positional=st.one_of(st.integers(), st.text()),
    named=st.one_of(st.integers(), st.text(), st.none()),
    kwargs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        max_size=3
    )
)
def test_kwargs_run(positional, named, kwargs):
    """Test that Kwargs.run returns correct tuple."""
    kw = tc.Kwargs()
    result = kw.run(positional, named=named, **kwargs)
    
    assert result[0] == positional
    assert result[1] == named
    assert result[2] == kwargs


@given(
    positional=st.integers()
)
def test_kwargs_run_defaults(positional):
    """Test Kwargs.run with default named parameter."""
    kw = tc.Kwargs()
    result = kw.run(positional)
    
    assert result[0] == positional
    assert result[1] is None
    assert result[2] == {}


@given(
    mixed_items=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=1, max_size=5),
            st.lists(st.integers(), min_size=1, max_size=3)
        ),
        min_size=2,
        max_size=10
    )
)
def test_varargs_cumsums_mixed_types(mixed_items):
    """Test cumsums with mixed types that support addition."""
    va = tc.VarArgs()
    
    # Filter to only compatible type sequences
    # Strings can add with strings, numbers with numbers, lists with lists
    first_type = type(mixed_items[0])
    
    if first_type in (int, float):
        # Keep only numbers
        items = [x for x in mixed_items if isinstance(x, (int, float))]
    elif first_type == str:
        # Keep only strings
        items = [x for x in mixed_items if isinstance(x, str)]
    elif first_type == list:
        # Keep only lists
        items = [x for x in mixed_items if isinstance(x, list)]
    else:
        return  # Skip other types
    
    if len(items) < 2:
        return  # Need at least 2 items
    
    result = va.cumsums(*items)
    
    # Verify cumulative behavior
    accumulated = None
    for i, item in enumerate(items):
        if accumulated is None:
            accumulated = item
        else:
            accumulated = accumulated + item
        
        if isinstance(accumulated, float):
            assert math.isclose(result[i], accumulated, rel_tol=1e-9)
        else:
            assert result[i] == accumulated