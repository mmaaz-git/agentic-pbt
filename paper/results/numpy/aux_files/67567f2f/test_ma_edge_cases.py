"""Test edge cases and corner conditions in numpy.ma."""

import numpy as np
import numpy.ma as ma
from hypothesis import given, strategies as st, assume, settings
import warnings


# Test for potential inconsistency between different mask operations
@given(st.lists(st.integers(), min_size=5, max_size=5))
def test_mask_operations_consistency(data):
    """Test consistency between different ways of masking."""
    arr = ma.array(data)
    
    # Method 1: Direct mask assignment
    arr1 = arr.copy()
    arr1.mask = [True, False, True, False, True]
    
    # Method 2: Using masked_where
    arr2 = ma.masked_where([True, False, True, False, True], data)
    
    # Method 3: Item assignment
    arr3 = arr.copy()
    arr3[0] = ma.masked
    arr3[2] = ma.masked
    arr3[4] = ma.masked
    
    # All three should produce same mask pattern
    assert arr1.mask[0] == arr2.mask[0] == arr3.mask[0] == True
    assert arr1.mask[1] == arr2.mask[1] == arr3.mask[1] == False
    assert arr1.mask[2] == arr2.mask[2] == arr3.mask[2] == True


# Test for transpose operations
@given(st.integers(2, 5), st.integers(2, 5))
def test_transpose_mask_preservation(rows, cols):
    """Test if transpose preserves mask structure correctly."""
    data = np.arange(rows * cols).reshape(rows, cols)
    mask = np.random.choice([True, False], size=(rows, cols))
    
    arr = ma.array(data, mask=mask)
    transposed = arr.T
    
    # Check mask is properly transposed
    for i in range(rows):
        for j in range(cols):
            assert mask[i, j] == transposed.mask[j, i]


# Test for potential issue in dot product
@given(st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False), min_size=3, max_size=3),
       st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False), min_size=3, max_size=3))
def test_dot_product_with_masks(vec1, vec2):
    """Test dot product behavior with masked values."""
    # Create masked arrays with one masked value each
    arr1 = ma.array(vec1, mask=[True, False, False])
    arr2 = ma.array(vec2, mask=[False, True, False])
    
    # Dot product should handle masks
    result = ma.dot(arr1, arr2)
    
    # Should be masked since we have masked values
    assert ma.is_masked(result)


# Test for ravel vs flatten
@given(st.integers(2, 4), st.integers(2, 4))
def test_ravel_vs_flatten(rows, cols):
    """Test if ravel and flatten behave consistently."""
    data = np.arange(rows * cols).reshape(rows, cols)
    mask = np.zeros((rows, cols), dtype=bool)
    mask[0, 0] = True
    
    arr = ma.array(data, mask=mask)
    
    raveled = arr.ravel()
    flattened = arr.flatten()
    
    # Both should produce same result
    assert np.array_equal(raveled.data, flattened.data)
    assert np.array_equal(raveled.mask, flattened.mask)


# Test for potential edge case in round
@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False), min_size=1, max_size=10))
def test_round_with_masks(data):
    """Test round function with masked arrays."""
    mask = [i % 2 == 0 for i in range(len(data))]
    arr = ma.array(data, mask=mask)
    
    # Round to nearest integer
    rounded = ma.round(arr)
    
    # Check non-masked values are properly rounded
    for i, val in enumerate(data):
        if not mask[i]:
            assert rounded[i] == round(val)
        else:
            assert rounded.mask[i] if hasattr(rounded.mask, '__getitem__') else rounded.mask


# Test for edge case in min/max with all masked
def test_min_max_all_masked():
    """Test min/max functions with fully masked array."""
    arr = ma.array([1, 2, 3, 4, 5], mask=True)
    
    # These should return masked values
    min_val = ma.min(arr)
    max_val = ma.max(arr)
    
    assert ma.is_masked(min_val)
    assert ma.is_masked(max_val)


# Test for potential issue in logical operations
@given(st.lists(st.booleans(), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10))
def test_logical_operations(data1, data2):
    """Test logical operations with masked arrays."""
    min_len = min(len(data1), len(data2))
    data1 = data1[:min_len]
    data2 = data2[:min_len]
    
    arr1 = ma.array(data1, mask=[False] * len(data1))
    arr2 = ma.array(data2, mask=[False] * len(data2))
    
    # Add some masks
    if len(data1) > 0:
        arr1.mask[0] = True
    if len(data2) > 1:
        arr2.mask[1] = True
    
    # Logical operations
    and_result = ma.logical_and(arr1, arr2)
    or_result = ma.logical_or(arr1, arr2)
    
    # Masked positions should remain masked
    assert and_result.mask[0] if hasattr(and_result.mask, '__getitem__') else and_result.mask
    assert or_result.mask[1] if hasattr(or_result.mask, '__getitem__') else or_result.mask


# Test for potential issue in reshaping
@given(st.integers(1, 20))
def test_reshape_mask_preservation(size):
    """Test if reshape preserves mask elements."""
    data = list(range(size))
    mask = [i % 3 == 0 for i in range(size)]
    arr = ma.array(data, mask=mask)
    
    # Find valid reshape dimensions
    for new_shape in [(size,), (1, size), (size, 1)]:
        reshaped = arr.reshape(new_shape)
        
        # Total masked count should be preserved
        assert ma.count_masked(reshaped) == sum(mask)


# Test for potential issue in take function
@given(st.lists(st.integers(0, 10), min_size=5, max_size=5),
       st.lists(st.integers(0, 4), min_size=1, max_size=3))
def test_take_function(data, indices):
    """Test take function with masked arrays."""
    mask = [i % 2 == 0 for i in range(len(data))]
    arr = ma.array(data, mask=mask)
    
    result = ma.take(arr, indices)
    
    # Check that masks are correctly taken
    for i, idx in enumerate(indices):
        assert result[i] == data[idx]
        assert result.mask[i] == mask[idx]


# Test for potential inconsistency in isin equivalent
@given(st.lists(st.integers(0, 10), min_size=1, max_size=10),
       st.lists(st.integers(0, 10), min_size=1, max_size=5))
def test_isin_equivalent(data, test_values):
    """Test if there's an isin equivalent that works correctly."""
    arr = ma.array(data, mask=[False] * len(data))
    
    # Manual isin check
    result = ma.array([val in test_values for val in data])
    
    # Add masks to some positions
    arr.mask[0] = True
    
    # Masked values should propagate
    for i in range(len(arr)):
        if arr.mask[i] if hasattr(arr.mask, '__getitem__') else arr.mask:
            # Can't determine if masked value is in test_values
            pass


# Test the compress corner case more thoroughly
def test_compress_argument_order():
    """Test ma.compress with different argument patterns."""
    arr = ma.array([1, 2, 3, 4, 5], mask=[0, 0, 1, 0, 0])
    condition = arr > 2  # Results in masked array [F, F, --, T, T]
    
    print("Testing compress with condition that includes masks...")
    print(f"Array: {arr}")
    print(f"Condition (arr > 2): {condition}")
    print(f"Condition type: {type(condition)}")
    
    # This might behave unexpectedly
    try:
        result = ma.compress(condition, arr)
        print(f"ma.compress(condition, arr): {result}")
        
        # Expected: elements where condition is True and not masked
        # So should be [4, 5]
        assert list(result) == [4, 5], f"Expected [4, 5], got {list(result)}"
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    # Run special test
    print("=" * 60)
    test_compress_argument_order()
    print("=" * 60)
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x", "-k", "not compress_argument"])