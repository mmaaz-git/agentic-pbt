"""Focused tests to find specific bugs in numpy.ma module."""

import numpy as np
import numpy.ma as ma
from hypothesis import given, strategies as st, assume, settings
import warnings


# Test for potential bugs in ma.compress function
@given(st.lists(st.integers(), min_size=1, max_size=20),
       st.lists(st.booleans(), min_size=1, max_size=20))
def test_compress_function_vs_method(data, mask):
    """Test if ma.compress function works correctly vs method."""
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    
    # Test function vs method
    try:
        # This might fail based on what we saw earlier
        result_func = ma.compress(~arr.mask, arr)  # Function form
        result_method = arr.compressed()  # Method form
        
        # They should be equivalent
        assert np.array_equal(result_func, result_method)
    except IndexError:
        # Found a bug!
        print(f"Bug found: ma.compress function fails with arr={arr}")
        raise


# Test for edge cases in ma.choose
@given(st.lists(st.integers(0, 5), min_size=1, max_size=10))
def test_choose_with_masked_choices(indices):
    """Test choose when choice arrays have masks."""
    # Create choice arrays with different mask patterns
    choices = [
        ma.array([10, 20, 30], mask=[True, False, False]),
        ma.array([100, 200, 300], mask=[False, True, False]),
        ma.array([1000, 2000, 3000], mask=[False, False, True])
    ]
    
    # Limit indices to valid range
    indices = [i % 3 for i in indices[:3]]
    indices = ma.array(indices)
    
    result = ma.choose(indices, choices)
    
    # Check if masks propagate correctly
    for i, idx in enumerate(indices):
        if i < len(result):
            choice_array = choices[idx]
            # The mask from the chosen array should propagate
            if choice_array.mask[i]:
                assert result.mask[i] if not np.isscalar(result.mask) else result.mask


# Test for potential overflow in integer operations
@given(st.integers(min_value=np.iinfo(np.int32).max - 100, 
                   max_value=np.iinfo(np.int32).max))
def test_integer_overflow_in_operations(large_int):
    """Test if integer operations handle overflow correctly."""
    arr1 = ma.array([large_int], dtype=np.int32)
    arr2 = ma.array([large_int], dtype=np.int32)
    
    # Addition might overflow
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ma.add(arr1, arr2)
        
        # Check if overflow is handled (might wrap or promote dtype)
        if result.dtype == np.int32:
            # If still int32, it should have wrapped
            expected = np.int32(large_int) + np.int32(large_int)
            assert result[0] == expected or result.mask[0]


# Test for ma.where with scalar inputs
@given(st.floats(allow_nan=False, allow_infinity=False),
       st.floats(allow_nan=False, allow_infinity=False))
def test_where_with_scalars(x_val, y_val):
    """Test ma.where with scalar inputs."""
    condition = np.array([True, False, True])
    
    # Using scalars for x and y
    result = ma.where(condition, x_val, y_val)
    
    # Check result
    assert len(result) == len(condition)
    for i, cond in enumerate(condition):
        if cond:
            assert result[i] == x_val
        else:
            assert result[i] == y_val


# Test for anomaly in fix_invalid
@given(st.lists(st.floats(allow_nan=True, allow_infinity=True), min_size=1, max_size=10))
def test_fix_invalid_preserves_valid(data):
    """Test that fix_invalid doesn't modify valid values."""
    arr = ma.array(data)
    fixed = ma.fix_invalid(arr, copy=True)
    
    for i, val in enumerate(data):
        if not (np.isnan(val) or np.isinf(val)):
            # Valid values should be preserved exactly
            if not fixed.mask[i] if hasattr(fixed.mask, '__getitem__') else not fixed.mask:
                assert fixed.data[i] == val


# Test append with incompatible shapes
@given(st.integers(2, 5), st.integers(2, 5))
def test_append_multidimensional(dim1, dim2):
    """Test append with multi-dimensional arrays."""
    arr1 = ma.array(np.ones((dim1, 3)))
    arr2 = ma.array(np.ones((dim2, 3)))
    
    # Append along axis 0 should work
    result = ma.append(arr1, arr2, axis=0)
    assert result.shape == (dim1 + dim2, 3)
    
    # Append without axis should flatten
    result_flat = ma.append(arr1, arr2)
    assert len(result_flat) == dim1 * 3 + dim2 * 3


# Test for masked_equal with NaN
@given(st.lists(st.floats(allow_nan=True, allow_infinity=False), min_size=1, max_size=10))
def test_masked_equal_with_nan(data):
    """Test masked_equal behavior with NaN values."""
    arr = ma.array(data)
    
    # Try to mask NaN values using masked_equal
    result = ma.masked_equal(arr, np.nan)
    
    # NaN != NaN, so masked_equal shouldn't mask NaN values
    nan_indices = [i for i, v in enumerate(data) if np.isnan(v)]
    for i in nan_indices:
        # NaN values should NOT be masked by masked_equal with np.nan
        if hasattr(result.mask, '__getitem__'):
            assert not result.mask[i]  # This might reveal unexpected behavior


# Test sort with all masked values
def test_sort_all_masked():
    """Test sort behavior when all values are masked."""
    arr = ma.array([3, 1, 4, 1, 5], mask=True)
    sorted_arr = arr.copy()
    sorted_arr.sort()
    
    # All should still be masked
    assert ma.is_masked(sorted_arr)
    if not np.isscalar(sorted_arr.mask):
        assert all(sorted_arr.mask)


# Special test for compress edge case
def test_compress_calling_convention():
    """Test the exact issue we found with ma.compress."""
    x = ma.array([1, 2, 3, 4, 5], mask=[0, 0, 1, 0, 0])
    
    # This should work (method form)
    result1 = x.compressed()
    assert list(result1) == [1, 2, 4, 5]
    
    # This might have issues (function form)
    try:
        # Using the exact call from documentation
        condition = ~x.mask
        result2 = ma.compress(condition, x)
        assert list(result2) == [1, 2, 4, 5]
    except Exception as e:
        print(f"Bug confirmed: ma.compress function fails: {e}")
        raise


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])