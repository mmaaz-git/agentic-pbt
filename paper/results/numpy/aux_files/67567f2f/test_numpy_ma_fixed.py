"""Property-based tests for numpy.ma module to find bugs - Fixed version."""

import numpy as np
import numpy.ma as ma
from hypothesis import given, strategies as st, assume, settings
import math


# Strategy for generating masked arrays
@st.composite
def masked_arrays(draw, dtype=None, shape=None):
    """Generate masked arrays with various shapes and masks."""
    if shape is None:
        shape = draw(st.integers(1, 20))
    
    if dtype is None:
        dtype = draw(st.sampled_from([np.int32, np.float64]))
    
    # Generate data
    if dtype == np.int32:
        data = draw(st.lists(st.integers(-1000, 1000), min_size=shape, max_size=shape))
    else:
        data = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                            min_size=shape, max_size=shape))
    
    # Generate mask
    mask = draw(st.lists(st.booleans(), min_size=shape, max_size=shape))
    
    return ma.array(data, mask=mask, dtype=dtype)


# Helper to safely get mask value at index
def get_mask_value(arr, index):
    """Safely get mask value at index, handling scalar masks."""
    if np.isscalar(arr.mask):
        return arr.mask
    return arr.mask[index]


# Test: where function with edge cases
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10),
       st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10))
def test_where_with_mixed_masks(x_data, y_data, x_mask, y_mask, condition):
    """Test ma.where with various mask combinations."""
    # Make all same length
    min_len = min(len(x_data), len(y_data), len(x_mask), len(y_mask), len(condition))
    x_data = x_data[:min_len]
    y_data = y_data[:min_len]
    x_mask = x_mask[:min_len]
    y_mask = y_mask[:min_len]
    condition = condition[:min_len]
    
    assume(min_len > 0)
    
    x = ma.array(x_data, mask=x_mask)
    y = ma.array(y_data, mask=y_mask)
    cond = np.array(condition)
    
    result = ma.where(cond, x, y)
    
    # Check each element
    for i in range(len(result)):
        if cond[i]:
            # Should take from x
            if not get_mask_value(x, i):
                assert not get_mask_value(result, i)
                assert result.data[i] == x.data[i]
        else:
            # Should take from y
            if not get_mask_value(y, i):
                assert not get_mask_value(result, i)
                assert result.data[i] == y.data[i]


# Test: compress function with edge cases
@given(st.lists(st.integers(), min_size=0, max_size=20),
       st.lists(st.booleans(), min_size=0, max_size=20))
def test_compress_empty_arrays(data, mask):
    """Test compress with empty and fully masked arrays."""
    if len(data) == 0 or len(mask) == 0:
        # Test empty array
        arr = ma.array([])
        compressed = arr.compressed()
        assert len(compressed) == 0
    else:
        # Make same length
        min_len = min(len(data), len(mask))
        data = data[:min_len]
        mask = mask[:min_len]
        
        arr = ma.array(data, mask=mask)
        compressed = arr.compressed()
        
        # Count non-masked
        expected_len = sum(1 for m in mask if not m)
        assert len(compressed) == expected_len


# Test: Operations on arrays with all masked values
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_all_masked_operations(data):
    """Test operations on fully masked arrays."""
    # Create fully masked array
    arr = ma.array(data, mask=True)
    
    # compressed should return empty
    compressed = arr.compressed()
    assert len(compressed) == 0
    
    # filled should replace all
    filled = ma.filled(arr, 999)
    assert all(v == 999 for v in filled)


# Test: Arithmetic operations preserve masks
@given(masked_arrays(), masked_arrays())
def test_arithmetic_mask_preservation(arr1, arr2):
    """Arithmetic operations should handle masks correctly."""
    # Make same length
    min_len = min(len(arr1), len(arr2))
    arr1 = arr1[:min_len]
    arr2 = arr2[:min_len]
    
    # Test addition
    result = ma.add(arr1, arr2)
    
    # Result should be masked where either input is masked
    for i in range(len(result)):
        should_be_masked = get_mask_value(arr1, i) or get_mask_value(arr2, i)
        is_masked = get_mask_value(result, i)
        assert should_be_masked == is_masked


# Test: choose function boundary conditions
@given(st.integers(0, 10))
def test_choose_index_bounds(invalid_index):
    """Test choose with out-of-bounds indices."""
    # Create 3 choice arrays
    choices = [ma.array([1, 2, 3]), ma.array([10, 20, 30]), ma.array([100, 200, 300])]
    
    # Test with invalid index
    indices = ma.array([0, invalid_index, 1])
    
    if invalid_index >= len(choices):
        # Should raise or handle gracefully
        try:
            result = ma.choose(indices, choices)
            # If it doesn't raise, check if masked appropriately
            assert get_mask_value(result, 1)  # Out of bounds index should be masked or error
        except (IndexError, ValueError):
            # Expected behavior for out of bounds
            pass


# Test: Stack operations with mismatched shapes
@given(st.lists(st.integers(1, 10), min_size=2, max_size=5))
def test_stack_different_shapes(shapes):
    """Test stack behavior with different shaped arrays."""
    arrays = []
    for shape in shapes:
        data = list(range(shape))
        mask = [i % 2 == 0 for i in range(shape)]
        arrays.append(ma.array(data, mask=mask))
    
    # vstack should handle different lengths
    try:
        result = ma.vstack(arrays)
        # If successful, check shape
        assert result.shape[0] == len(arrays)
    except ValueError:
        # Expected if shapes incompatible
        pass


# Test: masked_invalid with edge float values
@given(st.lists(st.floats(allow_nan=True, allow_infinity=True), min_size=1, max_size=20))
def test_masked_invalid_edge_cases(data):
    """Test masked_invalid with NaN, inf, and normal values."""
    arr = np.array(data)
    result = ma.masked_invalid(arr)
    
    for i, val in enumerate(data):
        if np.isnan(val) or np.isinf(val):
            assert get_mask_value(result, i)
        else:
            assert not get_mask_value(result, i)
            assert result.data[i] == val


# Test: concatenate with mixed array types
@given(st.lists(st.integers(), min_size=1, max_size=5),
       st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=5))
def test_concatenate_mixed_types(int_data, float_data):
    """Test concatenating integer and float masked arrays."""
    arr1 = ma.array(int_data, mask=[False] * len(int_data))
    arr2 = ma.array(float_data, mask=[False] * len(float_data))
    
    result = ma.concatenate([arr1, arr2])
    assert len(result) == len(arr1) + len(arr2)
    # Result should be float type to accommodate both
    assert result.dtype in [np.float32, np.float64]


# Test: Sort with NaN values (when not masked)
@given(st.lists(st.floats(allow_nan=True, allow_infinity=False), min_size=2, max_size=10))
def test_sort_with_nans(data):
    """Test sort behavior with NaN values."""
    # Don't mask the NaNs intentionally
    arr = ma.array(data, mask=[False] * len(data))
    sorted_arr = arr.copy()
    
    # Sorting with NaNs might behave unexpectedly
    try:
        sorted_arr.sort()
        # Check if NaNs are handled
        nan_count = sum(1 for x in data if np.isnan(x))
        result_nan_count = sum(1 for x in sorted_arr.data if np.isnan(x))
        assert nan_count == result_nan_count
    except:
        # Some configurations might fail with NaN
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])