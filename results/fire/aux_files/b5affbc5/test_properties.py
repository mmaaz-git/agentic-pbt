"""Property-based tests for fire.test_components module."""

import math
from hypothesis import given, strategies as st, assume
import fire.test_components as tc


# Test 1: multiplier_with_docstring should multiply correctly
@given(
    st.integers(min_value=-10**6, max_value=10**6),
    st.integers(min_value=-10**6, max_value=10**6)
)
def test_multiplier_with_docstring_multiplication(num, rate):
    """Test that multiplier_with_docstring actually multiplies num by rate."""
    result = tc.multiplier_with_docstring(num, rate)
    assert result == num * rate, f"Expected {num} * {rate} = {num * rate}, got {result}"


# Test 2: BinaryCanvas.move should wrap coordinates correctly
@given(
    st.integers(min_value=1, max_value=100),  # canvas size
    st.integers(min_value=-1000, max_value=1000),  # row
    st.integers(min_value=-1000, max_value=1000)   # col
)
def test_binary_canvas_move_wrapping(size, row, col):
    """Test that BinaryCanvas.move wraps coordinates using modulo."""
    canvas = tc.BinaryCanvas(size)
    canvas.move(row, col)
    
    # Check that the cursor position is wrapped correctly
    expected_row = row % size
    expected_col = col % size
    
    assert canvas._row == expected_row, f"Row {row} should wrap to {expected_row}, got {canvas._row}"
    assert canvas._col == expected_col, f"Col {col} should wrap to {expected_col}, got {canvas._col}"


# Test 3: BinaryCanvas set/on/off should update the correct pixel
@given(
    st.integers(min_value=1, max_value=50),  # canvas size  
    st.integers(min_value=0, max_value=49),  # row
    st.integers(min_value=0, max_value=49),  # col
    st.integers(min_value=0, max_value=10)   # value to set
)
def test_binary_canvas_set_updates_pixel(size, row, col, value):
    """Test that BinaryCanvas.set actually updates the pixel at the cursor position."""
    assume(row < size and col < size)
    
    canvas = tc.BinaryCanvas(size)
    canvas.move(row, col)
    canvas.set(value)
    
    assert canvas.pixels[row][col] == value, f"Pixel at ({row}, {col}) should be {value}, got {canvas.pixels[row][col]}"


# Test 4: identity function should return all arguments unchanged
@given(
    st.integers(),
    st.integers(),
    st.integers(),
    st.integers(),
    st.lists(st.integers(), max_size=5),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
)
def test_identity_returns_arguments(arg1, arg2, arg3, arg4, arg5_list, arg6_dict):
    """Test that identity returns all its arguments unchanged."""
    result = tc.identity(arg1, arg2, arg3, arg4, *arg5_list, **arg6_dict)
    
    assert result[0] == arg1, f"arg1: expected {arg1}, got {result[0]}"
    assert result[1] == arg2, f"arg2: expected {arg2}, got {result[1]}"
    assert result[2] == arg3, f"arg3: expected {arg3}, got {result[2]}"
    assert result[3] == arg4, f"arg4: expected {arg4}, got {result[3]}"
    assert result[4] == tuple(arg5_list), f"*args: expected {tuple(arg5_list)}, got {result[4]}"
    assert result[5] == arg6_dict, f"**kwargs: expected {arg6_dict}, got {result[5]}"


# Test 5: function_with_varargs should return the varargs
@given(
    st.integers(),
    st.integers(),
    st.integers(),
    st.lists(st.integers(), max_size=10)
)
def test_function_with_varargs_returns_varargs(arg1, arg2, arg3, varargs_list):
    """Test that function_with_varargs returns the unlimited positional args as claimed."""
    result = tc.function_with_varargs(arg1, arg2, arg3, *varargs_list)
    
    assert result == tuple(varargs_list), f"Expected varargs {tuple(varargs_list)}, got {result}"


# Test 6: fn_with_kwarg_and_defaults returns kwargs.get('arg3')
@given(
    st.integers(),
    st.integers(),
    st.booleans(),
    st.one_of(st.none(), st.integers(), st.text())
)
def test_fn_with_kwarg_and_defaults_returns_arg3(arg1, arg2, opt, arg3_value):
    """Test that fn_with_kwarg_and_defaults returns kwargs.get('arg3')."""
    if arg3_value is not None:
        result = tc.fn_with_kwarg_and_defaults(arg1, arg2, opt, arg3=arg3_value)
        assert result == arg3_value, f"Expected arg3={arg3_value}, got {result}"
    else:
        result = tc.fn_with_kwarg_and_defaults(arg1, arg2, opt)
        assert result is None, f"Expected None when arg3 not provided, got {result}"


# Test 7: function_with_keyword_arguments returns (arg1, kwargs)
@given(
    st.integers(),
    st.integers(),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
)
def test_function_with_keyword_arguments_return_format(arg1, arg2, kwargs_dict):
    """Test that function_with_keyword_arguments returns (arg1, kwargs) tuple."""
    result = tc.function_with_keyword_arguments(arg1, arg2, **kwargs_dict)
    
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-element tuple, got {len(result)} elements"
    assert result[0] == arg1, f"First element should be arg1={arg1}, got {result[0]}"
    assert result[1] == kwargs_dict, f"Second element should be kwargs={kwargs_dict}, got {result[1]}"


# Test 8: BinaryCanvas method chaining - all methods return self
@given(
    st.integers(min_value=5, max_value=20),
    st.lists(
        st.tuples(
            st.sampled_from(['move', 'on', 'off', 'set']),
            st.integers(min_value=0, max_value=19),
            st.integers(min_value=0, max_value=19),
            st.integers(min_value=0, max_value=1)
        ),
        min_size=1,
        max_size=10
    )
)
def test_binary_canvas_method_chaining(size, operations):
    """Test that BinaryCanvas methods return self for chaining."""
    canvas = tc.BinaryCanvas(size)
    
    for op_type, row, col, value in operations:
        if op_type == 'move':
            result = canvas.move(row, col)
            assert result is canvas, f"move() should return self"
        elif op_type == 'on':
            canvas.move(row, col)
            result = canvas.on()
            assert result is canvas, f"on() should return self"
        elif op_type == 'off':
            canvas.move(row, col)
            result = canvas.off()
            assert result is canvas, f"off() should return self"
        elif op_type == 'set':
            canvas.move(row, col)
            result = canvas.set(value)
            assert result is canvas, f"set() should return self"


# Test 9: BinaryCanvas on/off are equivalent to set(1)/set(0)
@given(
    st.integers(min_value=5, max_value=20),
    st.integers(min_value=0, max_value=19),
    st.integers(min_value=0, max_value=19)
)
def test_binary_canvas_on_off_equivalence(size, row, col):
    """Test that on() is equivalent to set(1) and off() is equivalent to set(0)."""
    assume(row < size and col < size)
    
    # Test on() == set(1)
    canvas1 = tc.BinaryCanvas(size)
    canvas1.move(row, col).on()
    
    canvas2 = tc.BinaryCanvas(size)
    canvas2.move(row, col).set(1)
    
    assert canvas1.pixels[row][col] == canvas2.pixels[row][col] == 1, \
        f"on() should be equivalent to set(1)"
    
    # Test off() == set(0)
    canvas3 = tc.BinaryCanvas(size)
    canvas3.move(row, col).off()
    
    canvas4 = tc.BinaryCanvas(size)
    canvas4.move(row, col).set(0)
    
    assert canvas3.pixels[row][col] == canvas4.pixels[row][col] == 0, \
        f"off() should be equivalent to set(0)"