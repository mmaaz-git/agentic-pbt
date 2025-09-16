"""Property-based tests for fire.test_components module."""

import math
from hypothesis import given, strategies as st, assume, settings
import fire.test_components as tc


@given(
    size=st.integers(min_value=1, max_value=100),
    row=st.integers(),
    col=st.integers()
)
def test_binary_canvas_move_modular_arithmetic(size, row, col):
    """Test that BinaryCanvas.move uses modular arithmetic correctly."""
    canvas = tc.BinaryCanvas(size=size)
    canvas.move(row, col)
    
    # The position should wrap around using modulo
    assert canvas._row == row % size
    assert canvas._col == col % size


@given(
    size=st.integers(min_value=1, max_value=50),
    operations=st.lists(
        st.tuples(
            st.integers(),  # row
            st.integers(),  # col
            st.sampled_from(['on', 'off', 'set_0', 'set_1'])
        ),
        min_size=1,
        max_size=100
    )
)
def test_binary_canvas_pixel_state_transitions(size, operations):
    """Test that pixel state transitions work correctly."""
    canvas = tc.BinaryCanvas(size=size)
    
    for row, col, operation in operations:
        canvas.move(row, col)
        actual_row = row % size
        actual_col = col % size
        
        if operation == 'on':
            canvas.on()
            assert canvas.pixels[actual_row][actual_col] == 1
        elif operation == 'off':
            canvas.off()
            assert canvas.pixels[actual_row][actual_col] == 0
        elif operation == 'set_0':
            canvas.set(0)
            assert canvas.pixels[actual_row][actual_col] == 0
        elif operation == 'set_1':
            canvas.set(1)
            assert canvas.pixels[actual_row][actual_col] == 1


@given(
    size=st.integers(min_value=1, max_value=50),
    value=st.integers(min_value=-1000, max_value=1000)
)
def test_binary_canvas_set_any_value(size, value):
    """Test that set() can store any integer value, not just 0/1."""
    canvas = tc.BinaryCanvas(size=size)
    canvas.move(0, 0)
    canvas.set(value)
    assert canvas.pixels[0][0] == value


@given(
    num=st.one_of(
        st.integers(min_value=-10000, max_value=10000),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    rate=st.one_of(
        st.integers(min_value=-100, max_value=100),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
    )
)
def test_multiplier_mathematical_property(num, rate):
    """Test that multiplier_with_docstring correctly multiplies."""
    result = tc.multiplier_with_docstring(num, rate)
    expected = num * rate
    
    if isinstance(result, float) or isinstance(expected, float):
        # Use approximate comparison for floats
        assert math.isclose(result, expected, rel_tol=1e-9)
    else:
        assert result == expected


@given(
    num=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_multiplier_default_rate(num):
    """Test that default rate is 2."""
    result = tc.multiplier_with_docstring(num)
    expected = num * 2
    
    if isinstance(result, float) or isinstance(expected, float):
        assert math.isclose(result, expected, rel_tol=1e-9)
    else:
        assert result == expected


@given(
    arg1=st.one_of(st.integers(), st.text(), st.none()),
    arg2=st.one_of(st.integers(), st.text(), st.none()),
    arg3=st.one_of(st.integers(), st.text(), st.none()),
    arg4=st.one_of(st.integers(), st.text(), st.none()),
    args=st.lists(st.integers(), max_size=5),
    kwargs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        max_size=3
    )
)
def test_identity_function_returns_arguments(arg1, arg2, arg3, arg4, args, kwargs):
    """Test that identity function returns all arguments unchanged."""
    result = tc.identity(arg1, arg2, arg3, arg4, *args, **kwargs)
    
    assert result[0] == arg1
    assert result[1] == arg2
    assert result[2] == arg3
    assert result[3] == arg4
    assert result[4] == tuple(args)
    assert result[5] == kwargs


@given(
    arg1=st.integers(),
    arg2=st.integers()
)
def test_identity_function_default_values(arg1, arg2):
    """Test that identity function has correct default values."""
    result = tc.identity(arg1, arg2)
    
    assert result[0] == arg1
    assert result[1] == arg2
    assert result[2] == 10  # default for arg3
    assert result[3] == 20  # default for arg4
    assert result[4] == ()  # empty tuple for *args
    assert result[5] == {}  # empty dict for **kwargs


@given(
    arg=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_bool_converter_type_invariant(arg):
    """Test that BoolConverter.as_bool always returns a bool."""
    converter = tc.BoolConverter()
    result = converter.as_bool(arg)
    assert isinstance(result, bool)


def test_bool_converter_default():
    """Test that BoolConverter.as_bool() returns False by default."""
    converter = tc.BoolConverter()
    result = converter.as_bool()
    assert result is False


@given(
    arg=st.one_of(
        st.just(0),
        st.just(1),
        st.just(""),
        st.just("text"),
        st.just([]),
        st.just([1, 2]),
        st.just({}),
        st.just({'a': 1})
    )
)
def test_bool_converter_follows_python_bool_rules(arg):
    """Test that as_bool follows Python's bool() conversion rules."""
    converter = tc.BoolConverter()
    result = converter.as_bool(arg)
    assert result == bool(arg)


def test_ordered_dictionary_empty():
    """Test that OrderedDictionary.empty() returns empty OrderedDict."""
    od = tc.OrderedDictionary()
    result = od.empty()
    assert len(result) == 0
    assert list(result.keys()) == []
    from collections import OrderedDict
    assert isinstance(result, OrderedDict)


def test_ordered_dictionary_non_empty():
    """Test that OrderedDictionary.non_empty() returns specific dict."""
    od = tc.OrderedDictionary()
    result = od.non_empty()
    
    # Check the documented structure
    assert 'A' in result
    assert result['A'] == 'A'
    assert 2 in result
    assert result[2] == 2
    
    # Check ordering is preserved
    assert list(result.keys()) == ['A', 2]


@given(st.data())
def test_circular_reference_creates_cycle(data):
    """Test that CircularReference.create() creates a self-referencing dict."""
    cr = tc.CircularReference()
    result = cr.create()
    
    # Check it's a dict with 'y' key
    assert isinstance(result, dict)
    assert 'y' in result
    
    # Check the circular reference
    assert result['y'] is result


def test_simple_set_returns_correct_set():
    """Test that simple_set returns the expected set."""
    result = tc.simple_set()
    assert result == {1, 2, 'three'}
    assert isinstance(result, set)


def test_simple_frozenset_returns_correct_frozenset():
    """Test that simple_frozenset returns the expected frozenset."""
    result = tc.simple_frozenset()
    assert result == frozenset({1, 2, 'three'})
    assert isinstance(result, frozenset)