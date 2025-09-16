import numpy as np
import math
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.floats(min_value=0, max_value=1e150, allow_nan=False, allow_infinity=False))
def test_sqrt_square_roundtrip(x):
    """Test that sqrt(square(x)) == abs(x) for non-negative numbers"""
    squared = np.square(x)
    if not np.isfinite(squared):
        return
    result = np.sqrt(squared)
    if x > 1e-154:
        assert np.allclose(result, x, rtol=1e-14), f"Failed for x={x}, got {result}"


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_sign_abs_identity(x):
    """Test that sign(x) * abs(x) == x for all finite numbers"""
    if x == 0:
        assert np.sign(x) * np.abs(x) == 0
    else:
        result = np.sign(x) * np.abs(x)
        assert np.allclose(result, x), f"Failed for x={x}, got {result}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False)
)
def test_clip_invariant(arr, min_val, max_val):
    """Test that clip always produces values within the specified range"""
    arr = np.array(arr)
    
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    clipped = np.clip(arr, min_val, max_val)
    
    assert np.all(clipped >= min_val), f"Some values below min: {clipped[clipped < min_val]}"
    assert np.all(clipped <= max_val), f"Some values above max: {clipped[clipped > max_val]}"
    
    in_range_mask = (arr >= min_val) & (arr <= max_val)
    assert np.allclose(clipped[in_range_mask], arr[in_range_mask]), "Changed values that were already in range"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_sort_preserves_elements(arr):
    """Test that sorting preserves all elements (just reorders them)"""
    arr = np.array(arr)
    sorted_arr = np.sort(arr)
    
    assert len(sorted_arr) == len(arr), "Sort changed array length"
    assert np.allclose(np.sort(arr), np.sort(sorted_arr)), "Sort changed the multiset of elements"


@given(st.floats(min_value=-1e150, max_value=1e150, allow_nan=False, allow_infinity=False))
def test_negative_involution(x):
    """Test that negative(negative(x)) == x"""
    result = np.negative(np.negative(x))
    assert np.allclose(result, x), f"Double negative failed for x={x}, got {result}"


@given(st.floats(min_value=-1e150, max_value=1e150, allow_nan=False, allow_infinity=False))
def test_positive_idempotent(x):
    """Test that positive(positive(x)) == positive(x)"""
    once = np.positive(x)
    twice = np.positive(once)
    assert np.allclose(once, twice), f"Positive not idempotent for x={x}"


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False)
)
def test_maximum_minimum_consistency(x, y):
    """Test that max(x,y) + min(x,y) == x + y"""
    max_val = np.maximum(x, y)
    min_val = np.minimum(x, y)
    
    if np.isfinite(x + y):
        assert np.allclose(max_val + min_val, x + y), f"max+min != x+y for x={x}, y={y}"


@given(st.integers(min_value=0, max_value=10))
def test_round_with_integers(decimals):
    """Test rounding with different decimal places"""
    values = np.array([1.234567, -2.345678, 0.0, 100.999])
    rounded = np.round(values, decimals)
    
    for i, val in enumerate(values):
        expected = round(val, decimals)
        assert np.allclose(rounded[i], expected), f"Rounding mismatch at index {i}"


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_floor_ceil_relationship(x):
    """Test that floor(x) <= x <= ceil(x)"""
    floor_val = np.floor(x)
    ceil_val = np.ceil(x)
    
    assert floor_val <= x, f"floor({x}) = {floor_val} > {x}"
    assert x <= ceil_val, f"ceil({x}) = {ceil_val} < {x}"
    assert ceil_val - floor_val <= 1.0001, f"ceil-floor > 1 for x={x}"


@given(
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=2, max_size=100),
    st.integers(min_value=1, max_value=10)
)
def test_reshape_preserves_data(data, ncols):
    """Test that reshape preserves all data elements"""
    arr = np.array(data)
    nrows = len(data) // ncols
    
    if nrows * ncols != len(data):
        return
    
    reshaped = arr.reshape(nrows, ncols)
    flattened = reshaped.flatten()
    
    assert np.array_equal(flattened, arr), "Reshape/flatten round trip failed"


@given(
    st.integers(min_value=2, max_value=10),
    st.integers(min_value=2, max_value=10),
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=4, max_size=100)
)
def test_transpose_involution(rows, cols, data):
    """Test that transpose(transpose(x)) == x"""
    if len(data) < rows * cols:
        return
    data = data[:rows * cols]
    arr = np.array(data).reshape(rows, cols)
    transposed_twice = np.transpose(np.transpose(arr))
    assert np.allclose(transposed_twice, arr), "Double transpose doesn't return original"


@given(st.floats(min_value=1e-300, max_value=1e-150, allow_nan=False, allow_infinity=False))
def test_tiny_number_sqrt_square(x):
    """Test sqrt/square with very small positive numbers"""
    squared = np.square(x)
    if squared == 0:
        return
    
    result = np.sqrt(squared)
    if result != 0:
        relative_error = abs(result - x) / x
        assert relative_error < 1e-10, f"Large relative error {relative_error} for x={x}"


@given(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != 0),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != 0)
)
def test_copysign_properties(x, y):
    """Test copysign properties"""
    result = np.copysign(x, y)
    
    assert np.abs(result) == np.abs(x), f"copysign changed magnitude"
    assert np.sign(result) == np.sign(y), f"copysign didn't copy sign correctly"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_argmax_argmin_consistency(arr):
    """Test that arr[argmax(arr)] == max(arr) and arr[argmin(arr)] == min(arr)"""
    arr = np.array(arr)
    
    max_idx = np.argmax(arr)
    min_idx = np.argmin(arr)
    
    assert np.allclose(arr[max_idx], np.max(arr)), "argmax doesn't point to maximum"
    assert np.allclose(arr[min_idx], np.min(arr)), "argmin doesn't point to minimum"


if __name__ == "__main__":
    print("Running property-based tests for NumPy core functions...")
    pytest.main([__file__, "-v", "--tb=short"])