"""Property-based tests for numpy.ma module to find bugs."""

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


@st.composite
def compatible_masked_arrays_pair(draw):
    """Generate two masked arrays with the same length."""
    length = draw(st.integers(1, 20))
    dtype = draw(st.sampled_from([np.int32, np.float64]))
    
    arr1 = draw(masked_arrays(dtype=dtype, shape=length))
    arr2 = draw(masked_arrays(dtype=dtype, shape=length))
    
    return arr1, arr2


# Test 1: Compressed array length property
@given(masked_arrays())
def test_compressed_length_property(arr):
    """compressed() should return array with length <= original."""
    compressed = arr.compressed()
    assert len(compressed) <= len(arr)
    # Also check that compressed has no masked values
    assert ma.count_masked(compressed) == 0


# Test 2: Concatenate length property
@given(st.lists(masked_arrays(), min_size=2, max_size=5))
def test_concatenate_length_property(arrays):
    """Concatenated array should have length equal to sum of inputs."""
    # Ensure all arrays have same dtype
    dtype = arrays[0].dtype
    arrays = [ma.array(arr, dtype=dtype) for arr in arrays]
    
    result = ma.concatenate(arrays)
    expected_length = sum(len(arr) for arr in arrays)
    assert len(result) == expected_length


# Test 3: Sort preserves set of non-masked values
@given(masked_arrays())
def test_sort_preserves_values(arr):
    """Sorting should preserve the set of non-masked values."""
    original_values = set(arr.compressed())
    sorted_arr = arr.copy()
    sorted_arr.sort()
    sorted_values = set(sorted_arr.compressed())
    assert original_values == sorted_values


# Test 4: masked_where round-trip property
@given(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def test_masked_where_roundtrip(data):
    """masked_where followed by filled should be recoverable for non-masked values."""
    arr = np.array(data)
    threshold = 0
    
    masked = ma.masked_where(arr > threshold, arr)
    filled = ma.filled(masked, 999999)
    
    # Check that non-masked values are preserved
    for i, val in enumerate(arr):
        if val <= threshold:
            assert filled[i] == val


# Test 5: where function mask propagation
@given(compatible_masked_arrays_pair(), st.lists(st.booleans(), min_size=1, max_size=20))
def test_where_mask_propagation(arrays, condition):
    """ma.where should properly propagate masks from both arrays."""
    x, y = arrays
    # Make condition array same length as x and y
    condition = condition[:len(x)]
    if len(condition) < len(x):
        condition.extend([False] * (len(x) - len(condition)))
    condition = np.array(condition)
    
    result = ma.where(condition, x, y)
    
    # Check mask propagation: if either source is masked, result should be masked
    for i in range(len(result)):
        if condition[i]:
            # Should take from x
            assert result.mask[i] == x.mask[i]
        else:
            # Should take from y
            assert result.mask[i] == y.mask[i]


# Test 6: append function length property
@given(masked_arrays(), masked_arrays())
def test_append_length(arr1, arr2):
    """Appending arrays should result in correct length."""
    result = ma.append(arr1, arr2)
    assert len(result) == len(arr1) + len(arr2)


# Test 7: filled function with default fill_value
@given(masked_arrays())
def test_filled_default_value(arr):
    """filled() should replace masked values with fill_value."""
    fill_value = 999999
    filled = ma.filled(arr, fill_value)
    
    # Check that all masked positions have fill_value
    for i in range(len(arr)):
        if arr.mask[i] if hasattr(arr.mask, '__getitem__') else arr.mask:
            assert filled[i] == fill_value


# Test 8: Testing fix_invalid function
@given(st.lists(st.floats(allow_nan=True, allow_infinity=True), min_size=1, max_size=20))
def test_fix_invalid(data):
    """fix_invalid should mask NaN and inf values."""
    arr = ma.array(data)
    fixed = ma.fix_invalid(arr)
    
    for i, val in enumerate(data):
        if math.isnan(val) or math.isinf(val):
            # Should be masked
            assert fixed.mask[i] if hasattr(fixed.mask, '__getitem__') else fixed.mask


# Test 9: Choose function with masked indices
@given(st.integers(2, 5))
def test_choose_with_masks(n_choices):
    """choose should handle masked indices correctly."""
    # Create indices with some masked values
    indices_data = [i % n_choices for i in range(10)]
    indices_mask = [i % 3 == 0 for i in range(10)]
    indices = ma.array(indices_data, mask=indices_mask)
    
    # Create choice arrays
    choices = [ma.array(range(i*10, i*10 + 10)) for i in range(n_choices)]
    
    result = ma.choose(indices, choices)
    
    # Check that masked indices lead to masked results
    for i in range(len(indices)):
        if indices.mask[i] if hasattr(indices.mask, '__getitem__') else indices.mask:
            assert result.mask[i] if hasattr(result.mask, '__getitem__') else result.mask


# Test 10: stack operations preserve array properties
@given(st.lists(masked_arrays(shape=5), min_size=2, max_size=4))
def test_stack_preserves_masks(arrays):
    """stack should preserve mask information."""
    # Ensure all arrays have same shape and dtype
    dtype = arrays[0].dtype
    shape = arrays[0].shape[0] if hasattr(arrays[0].shape, '__getitem__') else len(arrays[0])
    
    arrays = [ma.array(arr.data[:shape], mask=arr.mask[:shape], dtype=dtype) for arr in arrays]
    
    stacked = ma.stack(arrays)
    
    # Check dimensions
    assert stacked.shape[0] == len(arrays)
    
    # Check that masks are preserved
    for i, arr in enumerate(arrays):
        for j in range(len(arr)):
            arr_mask = arr.mask[j] if hasattr(arr.mask, '__getitem__') else arr.mask
            stacked_mask = stacked.mask[i, j] if hasattr(stacked.mask, '__getitem__') else stacked.mask
            assert arr_mask == stacked_mask


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])