"""Property-based tests for fire.test_components module"""

import math
from hypothesis import given, strategies as st, assume, settings
import fire.test_components as target


@given(
    size=st.integers(min_value=1, max_value=100),
    row=st.integers(),
    col=st.integers()
)
def test_binary_canvas_modulo_wrapping(size, row, col):
    """Test that BinaryCanvas.move() correctly wraps coordinates using modulo."""
    canvas = target.BinaryCanvas(size=size)
    canvas.move(row, col)
    
    # The cursor position should be wrapped using modulo
    assert canvas._row == row % size
    assert canvas._col == col % size
    
    # Moving to row+size or col+size should result in the same position
    canvas2 = target.BinaryCanvas(size=size)
    canvas2.move(row + size, col + size)
    assert canvas._row == canvas2._row
    assert canvas._col == canvas2._col


@given(
    size=st.integers(min_value=1, max_value=50),
    positions=st.lists(
        st.tuples(st.integers(), st.integers(), st.integers(min_value=0, max_value=1)),
        min_size=1,
        max_size=100
    )
)
def test_binary_canvas_set_get_consistency(size, positions):
    """Test that setting pixels maintains state correctly."""
    canvas = target.BinaryCanvas(size=size)
    
    # Set pixels at various positions
    for row, col, value in positions:
        canvas.move(row, col).set(value)
    
    # Verify the last set value at each unique position
    position_map = {}
    for row, col, value in positions:
        actual_row = row % size
        actual_col = col % size
        position_map[(actual_row, actual_col)] = value
    
    for (row, col), expected_value in position_map.items():
        assert canvas.pixels[row][col] == expected_value


@given(divisor=st.floats(allow_nan=False, allow_infinity=False))
def test_number_defaults_reciprocal_property(divisor):
    """Test mathematical property: reciprocal(x) * x should equal 1 (for non-zero x)."""
    assume(abs(divisor) > 1e-10)  # Avoid division by values too close to zero
    
    obj = target.NumberDefaults()
    result = obj.reciprocal(divisor)
    
    # reciprocal(x) * x should equal 1
    assert math.isclose(result * divisor, 1.0, rel_tol=1e-9)


@given(divisor=st.integers())
def test_number_defaults_integer_reciprocal_property(divisor):
    """Test integer reciprocal mathematical property."""
    assume(divisor != 0)  # Avoid division by zero
    
    obj = target.NumberDefaults()
    result = obj.integer_reciprocal(divisor)
    
    # integer_reciprocal(x) * x should equal 1.0
    assert math.isclose(result * divisor, 1.0, rel_tol=1e-9)


@given(
    items=st.lists(st.integers(min_value=-1000, max_value=1000))
)
def test_varargs_cumsums_property(items):
    """Test that cumsums returns correct cumulative sums."""
    obj = target.VarArgs()
    result = obj.cumsums(*items)
    
    # Result length should match input length
    if items:
        assert len(result) == len(items)
        
        # Each element should be the sum of all previous elements
        cumsum = 0
        for i, item in enumerate(items):
            cumsum += item
            assert result[i] == cumsum
    else:
        assert result == []


@given(
    items=st.lists(st.text(min_size=1, max_size=10))
)
def test_varargs_cumsums_string_concatenation(items):
    """Test cumsums with strings (should concatenate)."""
    assume(len(items) > 0)
    
    obj = target.VarArgs()
    result = obj.cumsums(*items)
    
    assert len(result) == len(items)
    
    # For strings, + means concatenation
    concat = ""
    for i, item in enumerate(items):
        concat += item
        assert result[i] == concat


@given(
    num=st.integers(min_value=-10000, max_value=10000),
    rate=st.integers(min_value=-100, max_value=100)
)
def test_multiplier_with_docstring_property(num, rate):
    """Test that multiplier_with_docstring correctly multiplies."""
    result = target.multiplier_with_docstring(num, rate)
    assert result == num * rate


@given(num=st.integers())
def test_multiplier_identity_property(num):
    """Test identity property: multiplying by 1 returns the original number."""
    result = target.multiplier_with_docstring(num, 1)
    assert result == num


@given(num=st.integers())
def test_multiplier_zero_property(num):
    """Test zero property: multiplying by 0 returns 0."""
    result = target.multiplier_with_docstring(num, 0)
    assert result == 0


def test_circular_reference_property():
    """Test that CircularReference creates a self-referencing dictionary."""
    obj = target.CircularReference()
    result = obj.create()
    
    # The dictionary should reference itself
    assert isinstance(result, dict)
    assert 'y' in result
    assert result['y'] is result  # Should be the same object


@given(
    alpha=st.integers(),
    beta=st.integers(),
    chars=st.lists(st.text(min_size=1, max_size=1))
)
def test_varargs_varchars_property(alpha, beta, chars):
    """Test VarArgs.varchars returns correct tuple structure."""
    obj = target.VarArgs()
    result = obj.varchars(alpha, beta, *chars)
    
    assert len(result) == 3
    assert result[0] == alpha
    assert result[1] == beta
    assert result[2] == ''.join(chars)


@given(
    arg1=st.integers(),
    arg2=st.integers(),
    arg3=st.integers(),
    arg4=st.integers(),
    arg5=st.lists(st.integers()),
    arg6=st.dictionaries(st.text(), st.integers())
)
def test_identity_function_property(arg1, arg2, arg3, arg4, arg5, arg6):
    """Test that identity function returns all arguments correctly."""
    result = target.identity(arg1, arg2, arg3, arg4, *arg5, **arg6)
    
    assert result[0] == arg1
    assert result[1] == arg2
    assert result[2] == arg3
    assert result[3] == arg4
    assert result[4] == tuple(arg5)
    assert result[5] == arg6


@given(size=st.integers(min_value=1, max_value=100))
def test_binary_canvas_on_off_consistency(size):
    """Test that on() sets to 1 and off() sets to 0."""
    canvas = target.BinaryCanvas(size=size)
    
    # Test on()
    canvas.move(0, 0).on()
    assert canvas.pixels[0][0] == 1
    
    # Test off()
    canvas.off()
    assert canvas.pixels[0][0] == 0
    
    # Test chaining with wrapped positions
    canvas.move(1, 1).on().move(2, 2).off()
    # Positions should wrap with modulo
    pos1_row, pos1_col = 1 % size, 1 % size
    pos2_row, pos2_col = 2 % size, 2 % size
    
    # If the two positions are the same, the last operation wins
    if (pos1_row, pos1_col) == (pos2_row, pos2_col):
        assert canvas.pixels[pos1_row][pos1_col] == 0  # off() was last
    else:
        assert canvas.pixels[pos1_row][pos1_col] == 1
        assert canvas.pixels[pos2_row][pos2_col] == 0