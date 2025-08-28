"""Search for critical bugs in numpy.ma core functionality."""

import numpy as np
import numpy.ma as ma
from hypothesis import given, strategies as st, assume, settings, example
import warnings


# Test for potential issue in getdata
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_getdata_vs_data_attribute(data):
    """Test if getdata function matches .data attribute."""
    arr = ma.array(data, mask=[i % 2 == 0 for i in range(len(data))])
    
    # These should be equivalent
    data_attr = arr.data
    data_func = ma.getdata(arr)
    
    assert np.array_equal(data_attr, data_func)


# Test for potential inconsistency in count
@given(st.lists(st.integers(), min_size=1, max_size=20),
       st.lists(st.booleans(), min_size=1, max_size=20))
def test_count_consistency(data, mask):
    """Test if count functions are consistent."""
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    
    # Different ways to count
    count1 = arr.count()
    count2 = ma.count(arr)
    count3 = len(arr) - ma.count_masked(arr)
    
    assert count1 == count2 == count3


# Test for resize function
@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_resize_preserves_mask(data):
    """Test if resize preserves mask pattern correctly."""
    mask = [i % 2 == 0 for i in range(len(data))]
    arr = ma.array(data, mask=mask)
    
    # Resize to larger
    new_size = len(data) * 2
    resized = ma.resize(arr, new_size)
    
    # Check that pattern repeats
    for i in range(new_size):
        orig_idx = i % len(data)
        if hasattr(resized.mask, '__getitem__'):
            assert resized.mask[i] == mask[orig_idx]


# Test for potential issue with nonzero
@given(st.lists(st.integers(-5, 5), min_size=1, max_size=20))
def test_nonzero_with_masks(data):
    """Test nonzero function with masked arrays."""
    mask = [abs(x) <= 1 for x in data]  # Mask small values
    arr = ma.array(data, mask=mask)
    
    # Get non-zero indices
    nonzero_indices = ma.nonzero(arr)
    
    # Verify: should only include non-zero AND non-masked
    for idx in nonzero_indices[0]:
        assert data[idx] != 0
        assert not mask[idx]


# Test for edge case in any/all functions
def test_any_all_empty():
    """Test any/all with empty masked array."""
    arr = ma.array([])
    
    # Empty array behavior
    result_any = ma.any(arr)
    result_all = ma.all(arr)
    
    # NumPy convention: any([]) = False, all([]) = True
    assert result_any == False
    assert result_all == True


# Test for potential issue in flatten
@given(st.integers(2, 5), st.integers(2, 5))
def test_flatten_preserves_masks(rows, cols):
    """Test if flatten preserves all masks."""
    # Create 2D masked array
    data = np.arange(rows * cols).reshape(rows, cols)
    mask = np.zeros((rows, cols), dtype=bool)
    mask[0, 0] = True
    mask[-1, -1] = True
    
    arr = ma.array(data, mask=mask)
    flattened = arr.flatten()
    
    # Check mask preservation
    assert flattened.mask[0] == True
    assert flattened.mask[-1] == True
    assert ma.count_masked(flattened) == 2


# Test for potential edge case in set operations
@given(st.lists(st.integers(0, 10), min_size=1, max_size=10),
       st.lists(st.integers(0, 10), min_size=1, max_size=10))
def test_setdiff1d(data1, data2):
    """Test setdiff1d with masked arrays."""
    # Add some masks
    arr1 = ma.array(data1, mask=[i % 3 == 0 for i in range(len(data1))])
    arr2 = ma.array(data2, mask=[i % 2 == 0 for i in range(len(data2))])
    
    try:
        result = ma.setdiff1d(arr1, arr2)
        
        # Result should only contain unmasked values from arr1 not in arr2
        unmasked1 = set(arr1.compressed())
        unmasked2 = set(arr2.compressed())
        expected = sorted(unmasked1 - unmasked2)
        
        assert list(result) == expected
    except AttributeError:
        # setdiff1d might not be available
        pass


# Test for anomaly in var/std functions
@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False), min_size=2, max_size=20))
def test_var_std_with_masks(data):
    """Test variance and standard deviation with masked values."""
    mask = [i % 3 == 0 for i in range(len(data))]
    arr = ma.array(data, mask=mask)
    
    if arr.count() > 1:  # Need at least 2 unmasked values
        var = ma.var(arr)
        std = ma.std(arr)
        
        # std should be sqrt of variance
        assert np.isclose(std, np.sqrt(var), rtol=1e-10)
        
        # Compare with numpy on unmasked values
        unmasked = arr.compressed()
        expected_var = np.var(unmasked)
        expected_std = np.std(unmasked)
        
        assert np.isclose(var, expected_var, rtol=1e-10)
        assert np.isclose(std, expected_std, rtol=1e-10)


# Test for edge case in cumprod
@given(st.lists(st.floats(min_value=0.1, max_value=2.0, allow_nan=False), min_size=1, max_size=10))
def test_cumprod_with_masks(data):
    """Test cumulative product with masked values."""
    mask = [i % 3 == 1 for i in range(len(data))]
    arr = ma.array(data, mask=mask)
    
    result = ma.cumprod(arr)
    
    # Check cumulative product skips masked values
    expected = []
    prod = 1.0
    for i, val in enumerate(data):
        if not mask[i]:
            prod *= val
        expected.append(prod if not mask[i] else 0)  # 0 as placeholder for masked
    
    for i in range(len(result)):
        if not mask[i]:
            assert np.isclose(result.data[i], expected[i], rtol=1e-10)


# Special test for a subtle bug in setting mask values
def test_mask_assignment_bug():
    """Test for potential bug in mask assignment."""
    arr = ma.array([1, 2, 3, 4, 5])
    
    # Initially no mask (or all False)
    assert not ma.is_masked(arr) or not any(arr.mask)
    
    # Set single mask value
    arr.mask = [True, False, False, False, False]
    assert arr.mask[0] == True
    
    # Now try to modify mask in place
    arr.mask[2] = True
    assert arr.mask[2] == True
    
    # This should work but might have issues
    arr[3] = ma.masked
    assert arr.mask[3] == True


# Test for edge case in ma.sqrt with negative values
@given(st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False), min_size=1, max_size=10))
def test_sqrt_negative_handling(data):
    """Test sqrt function with negative values."""
    arr = ma.array(data)
    
    # sqrt of negative should be masked
    result = ma.sqrt(arr)
    
    for i, val in enumerate(data):
        if val < 0:
            # Should be masked
            assert result.mask[i] if hasattr(result.mask, '__getitem__') else result.mask
        elif val >= 0:
            # Should not be masked and correct value
            if not (result.mask[i] if hasattr(result.mask, '__getitem__') else result.mask):
                assert np.isclose(result[i], np.sqrt(val), rtol=1e-10)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])