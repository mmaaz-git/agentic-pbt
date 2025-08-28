"""Extended property-based tests with more examples."""

import math
from hypothesis import given, strategies as st, settings
import fire.test_components as tc


@settings(max_examples=1000)
@given(
    size=st.integers(min_value=1, max_value=100),
    row=st.integers(min_value=-10000, max_value=10000),
    col=st.integers(min_value=-10000, max_value=10000)
)
def test_binary_canvas_move_extreme_values(size, row, col):
    """Test BinaryCanvas.move with extreme row/col values."""
    canvas = tc.BinaryCanvas(size=size)
    canvas.move(row, col)
    
    assert canvas._row == row % size
    assert canvas._col == col % size
    assert 0 <= canvas._row < size
    assert 0 <= canvas._col < size


@settings(max_examples=500)
@given(
    num=st.floats(allow_nan=True, allow_infinity=True),
    rate=st.floats(allow_nan=True, allow_infinity=True)
)
def test_multiplier_with_special_floats(num, rate):
    """Test multiplier with NaN and infinity."""
    result = tc.multiplier_with_docstring(num, rate)
    expected = num * rate
    
    # Test that NaN and infinity are handled consistently with Python
    if math.isnan(expected):
        assert math.isnan(result)
    elif math.isinf(expected):
        assert math.isinf(result)
        assert (result > 0) == (expected > 0)  # Same sign of infinity
    else:
        if not (math.isnan(result) or math.isnan(expected)):
            assert math.isclose(result, expected, rel_tol=1e-9, abs_tol=1e-9)