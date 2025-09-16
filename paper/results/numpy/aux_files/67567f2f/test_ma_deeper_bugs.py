"""Deeper investigation for bugs in numpy.ma module."""

import numpy as np
import numpy.ma as ma
from hypothesis import given, strategies as st, assume, settings
import warnings


# Test mathematical operations with edge cases
@given(st.floats(min_value=1e-100, max_value=1e-90, allow_nan=False))
def test_divide_by_small_numbers(small_val):
    """Test division operations with very small numbers."""
    arr1 = ma.array([1.0])
    arr2 = ma.array([small_val])
    
    result = ma.divide(arr1, arr2)
    
    # Should not be masked unless overflow
    if not np.isinf(result[0]):
        assert not result.mask[0] if hasattr(result.mask, '__getitem__') else not result.mask


# Test power operation edge cases
@given(st.floats(min_value=-10, max_value=-0.1, allow_nan=False),
       st.floats(min_value=0.1, max_value=10, allow_nan=False))
def test_power_negative_base(base, exponent):
    """Test power operation with negative base and non-integer exponent."""
    arr_base = ma.array([base])
    arr_exp = ma.array([exponent])
    
    # Negative base with non-integer exponent should produce complex or masked
    result = ma.power(arr_base, arr_exp)
    
    # This should either be masked or complex
    if not np.iscomplex(result[0]):
        # Should be masked as invalid
        assert result.mask[0] if hasattr(result.mask, '__getitem__') else result.mask


# Test for potential bug in ma.median
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), 
                min_size=1, max_size=20),
       st.lists(st.booleans(), min_size=1, max_size=20))
def test_median_with_masks(data, mask):
    """Test median calculation with masked values."""
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    
    # Only test if we have unmasked values
    if arr.count() > 0:
        median_val = ma.median(arr)
        
        # Median should be from unmasked values only
        unmasked = arr.compressed()
        expected_median = np.median(unmasked)
        
        assert np.isclose(median_val, expected_median, rtol=1e-10)


# Test cumulative functions with all masked
def test_cumsum_all_masked():
    """Test cumulative sum with all masked values."""
    arr = ma.array([1, 2, 3, 4, 5], mask=True)
    result = ma.cumsum(arr)
    
    # Result should be all masked
    assert ma.is_masked(result)
    if not np.isscalar(result.mask):
        assert all(result.mask)


# Test for argmax/argmin with all masked
def test_argmax_all_masked():
    """Test argmax with all masked values."""
    arr = ma.array([1, 2, 3, 4, 5], mask=True)
    
    try:
        result = ma.argmax(arr)
        # Should either return something sensible or raise
        assert False, f"Expected error, got {result}"
    except (ValueError, TypeError):
        # Expected behavior
        pass


# Test in-place operations
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10))
def test_inplace_operations(data, mask):
    """Test in-place operations preserve mask."""
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    original_mask = arr.mask.copy() if not np.isscalar(arr.mask) else arr.mask
    
    # In-place addition
    arr += 1
    
    # Mask should be preserved
    if not np.isscalar(original_mask):
        for i in range(len(arr)):
            assert (arr.mask[i] if hasattr(arr.mask, '__getitem__') else arr.mask) == original_mask[i]


# Test for edge case in ma.diff
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=10))
def test_diff_function(data):
    """Test diff function with various inputs."""
    arr = ma.array(data)
    
    # First difference
    diff1 = ma.diff(arr)
    assert len(diff1) == len(arr) - 1
    
    # Check values
    for i in range(len(diff1)):
        expected = data[i+1] - data[i]
        assert np.isclose(diff1[i], expected, rtol=1e-10)


# Test for clip function
@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False), min_size=1, max_size=10),
       st.floats(min_value=-50, max_value=0),
       st.floats(min_value=0, max_value=50))
def test_clip_function(data, vmin, vmax):
    """Test clip function behavior."""
    assume(vmin < vmax)
    
    arr = ma.array(data, mask=[False] * len(data))
    clipped = ma.clip(arr, vmin, vmax)
    
    for i, val in enumerate(data):
        expected = max(vmin, min(val, vmax))
        assert np.isclose(clipped[i], expected, rtol=1e-10)


# Test unique function with masked values
@given(st.lists(st.integers(0, 10), min_size=1, max_size=20),
       st.lists(st.booleans(), min_size=1, max_size=20))
def test_unique_with_masks(data, mask):
    """Test unique function with masked arrays."""
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    
    try:
        unique_vals = ma.unique(arr)
        
        # Should only include unique non-masked values
        unmasked = arr.compressed()
        expected_unique = np.unique(unmasked)
        
        assert len(unique_vals) == len(expected_unique)
        assert set(unique_vals.data) == set(expected_unique)
    except AttributeError:
        # ma.unique might not exist in all versions
        pass


# Special test for compress issue we found
def test_compress_detailed():
    """Detailed test of compress function behavior."""
    # Create test array
    x = ma.array([1, 2, 3, 4, 5], mask=[0, 0, 1, 0, 0])
    
    print("Testing ma.compress function...")
    
    # Get the condition
    condition = ~x.mask
    print(f"Array: {x}")
    print(f"Mask: {x.mask}")
    print(f"Condition (~mask): {condition}")
    
    # Try the compress function with different calling patterns
    try:
        # This is the documented way but might fail
        result1 = ma.compress(condition, x)
        print(f"ma.compress(condition, x) = {result1}")
    except Exception as e:
        print(f"ERROR with ma.compress(condition, x): {e}")
        
    try:
        # Try swapping arguments (wrong but might reveal issue)
        result2 = ma.compress(x, condition)
        print(f"ma.compress(x, condition) = {result2}")
    except Exception as e:
        print(f"ERROR with ma.compress(x, condition): {e}")
    
    # The method form that works
    result3 = x.compressed()
    print(f"x.compressed() = {result3}")


# Test for allclose function
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_allclose_with_masks(data):
    """Test allclose function behavior with masked arrays."""
    arr1 = ma.array(data, mask=[False] * len(data))
    arr2 = ma.array([x + 1e-10 for x in data], mask=[False] * len(data))
    
    # Should be close
    assert ma.allclose(arr1, arr2, rtol=1e-9)
    
    # Now mask some values
    arr1.mask[0] = True
    arr2.mask[0] = True
    
    # Should still be close (masked values ignored)
    assert ma.allclose(arr1, arr2, rtol=1e-9)


if __name__ == "__main__":
    # Run the detailed compress test
    print("=" * 60)
    test_compress_detailed()
    print("=" * 60)
    
    # Run hypothesis tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x", "-k", "not compress_detailed"])