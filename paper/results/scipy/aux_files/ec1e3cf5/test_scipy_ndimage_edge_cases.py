"""Edge case tests for scipy.ndimage - looking for boundary and extreme value bugs"""

import numpy as np
import scipy.ndimage as ndi
from hypothesis import given, strategies as st, assume, settings, note
import pytest
import warnings

# Test with extremely small arrays
@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=1, max_size=1))
@settings(max_examples=100)
def test_single_element_operations(data):
    """Operations on single-element arrays should work correctly"""
    arr = np.array(data)
    
    # These operations should work on single elements
    gaussian = ndi.gaussian_filter1d(arr, sigma=0)
    assert np.allclose(arr, gaussian)
    
    shifted = ndi.shift(arr, 0)
    assert np.allclose(arr, shifted)
    
    zoomed = ndi.zoom(arr, 1)
    assert np.allclose(arr, zoomed)

# Test with empty arrays
def test_empty_array_operations():
    """Operations on empty arrays should handle gracefully"""
    arr = np.array([])
    
    # These should either work or raise clear errors
    try:
        result = ndi.gaussian_filter1d(arr, sigma=1)
        assert len(result) == 0
    except (ValueError, IndexError) as e:
        # Should have clear error message
        assert len(str(e)) > 0

# Test filters with size larger than array
@given(st.lists(st.floats(min_value=-10, max_value=10, allow_nan=False),
                min_size=3, max_size=5))
@settings(max_examples=100) 
def test_filter_size_larger_than_array(data):
    """Filters with size > array size should handle edge effects properly"""
    arr = np.array(data)
    filter_size = len(arr) + 2
    
    # Median filter with size larger than array
    result = ndi.median_filter(arr, size=filter_size, mode='constant')
    
    # With constant mode, result should be heavily influenced by padding
    assert result.shape == arr.shape

# Test with arrays containing special patterns
@given(st.integers(min_value=5, max_value=20))
@settings(max_examples=100)
def test_checkerboard_pattern_filters(size):
    """Filters on checkerboard patterns should preserve structure properties"""
    # Create checkerboard pattern
    arr = np.zeros((size, size))
    arr[::2, ::2] = 1
    arr[1::2, 1::2] = 1
    
    # Median filter with size 2 on checkerboard
    result = ndi.median_filter(arr, size=2)
    
    # Result should have values between 0 and 1
    assert np.all(result >= 0)
    assert np.all(result <= 1)

# Test label with diagonal connectivity
@given(st.integers(min_value=3, max_value=10))
@settings(max_examples=100)
def test_label_diagonal_connectivity(size):
    """Label with different connectivity should give consistent results"""
    # Create diagonal line
    arr = np.eye(size, dtype=bool)
    
    # 4-connectivity (no diagonals)
    struct_4 = np.array([[0,1,0],[1,1,1],[0,1,0]])
    labels_4, num_4 = ndi.label(arr, structure=struct_4)
    
    # 8-connectivity (with diagonals) 
    struct_8 = np.ones((3,3))
    labels_8, num_8 = ndi.label(arr, structure=struct_8)
    
    # Diagonal should be 1 component with 8-connectivity
    assert num_8 == 1
    # But multiple components with 4-connectivity
    assert num_4 == size

# Test rotate with non-square arrays
@given(st.integers(min_value=3, max_value=8),
       st.integers(min_value=3, max_value=8))
@settings(max_examples=100)
def test_rotate_non_square(h, w):
    """Rotating non-square arrays by 90 degrees 4 times should return original"""
    assume(h != w)  # Ensure non-square
    arr = np.random.rand(h, w)
    
    # Rotate 90 degrees 4 times with reshape=True
    result = arr.copy()
    for _ in range(4):
        result = ndi.rotate(result, 90, reshape=True, order=1)
    
    # After 4 rotations, should be back to original shape and values
    assert result.shape == arr.shape
    # Values might differ due to interpolation
    assert np.allclose(arr, result, rtol=0.1, atol=0.1)

# Test affine transform with singular matrix
def test_affine_transform_singular_matrix():
    """Affine transform with singular matrix should handle gracefully"""
    arr = np.ones((5, 5))
    
    # Singular matrix (determinant = 0)
    singular_matrix = np.array([[1, 0], [0, 0]])
    
    # This should either work (projecting to line) or raise clear error
    try:
        result = ndi.affine_transform(arr, singular_matrix)
        # If it works, check result is valid
        assert result.shape == arr.shape
        assert not np.any(np.isnan(result))
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as e:
        # Should have meaningful error
        assert len(str(e)) > 0

# Test zoom with extreme factors
@given(st.floats(min_value=0.001, max_value=0.01))
@settings(max_examples=50)
def test_zoom_extreme_downscale(zoom_factor):
    """Extreme downscaling should handle gracefully"""
    arr = np.random.rand(100, 100)
    
    # Extreme downscaling
    result = ndi.zoom(arr, zoom_factor)
    
    # Result should be valid (small) array
    assert result.ndim == arr.ndim
    assert result.size > 0
    assert not np.any(np.isnan(result))

# Test distance transform on large sparse arrays
@given(st.integers(min_value=50, max_value=100))
@settings(max_examples=20)
def test_distance_transform_sparse(size):
    """Distance transform on sparse arrays should be efficient and correct"""
    # Very sparse array with single point
    arr = np.zeros((size, size), dtype=bool)
    arr[size//2, size//2] = True
    
    # All three distance transforms should give consistent results
    dist_bf = ndi.distance_transform_bf(arr)
    dist_cdt = ndi.distance_transform_cdt(arr)
    dist_edt = ndi.distance_transform_edt(arr)
    
    # All should have max at center
    assert dist_bf[size//2, size//2] == np.max(dist_bf)
    assert dist_cdt[size//2, size//2] == np.max(dist_cdt)
    assert dist_edt[size//2, size//2] == np.max(dist_edt)
    
    # EDT should be most accurate
    # BF and CDT should be close to EDT
    assert np.allclose(dist_bf, dist_edt, rtol=0.1, atol=1.0)
    assert np.allclose(dist_cdt, dist_edt, rtol=0.1, atol=1.0)

# Test morphology with custom structuring elements
@given(st.integers(min_value=5, max_value=15))
@settings(max_examples=50)
def test_morphology_custom_structure(size):
    """Morphological operations with custom structures should be consistent"""
    arr = np.random.rand(size, size) > 0.7
    
    # Cross-shaped structuring element
    cross = np.array([[0,1,0],[1,1,1],[0,1,0]])
    
    # Opening then closing should give similar result to closing then opening
    # (though not identical due to different order of operations)
    open_close = ndi.binary_closing(ndi.binary_opening(arr, cross), cross)
    close_open = ndi.binary_opening(ndi.binary_closing(arr, cross), cross)
    
    # They should be somewhat similar (same number of components at least)
    labels_oc, num_oc = ndi.label(open_close)
    labels_co, num_co = ndi.label(close_open)
    
    # Number of components shouldn't differ too much
    assert abs(num_oc - num_co) <= max(num_oc, num_co) // 2 + 1

# Test for NaN propagation
@given(st.integers(min_value=3, max_value=10))
@settings(max_examples=100)
def test_nan_propagation(size):
    """Operations should handle NaN values appropriately"""
    arr = np.ones((size, size))
    arr[size//2, size//2] = np.nan
    
    # Gaussian filter should propagate NaN
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ndi.gaussian_filter(arr, sigma=1)
    
    # Check that NaN affects surrounding area
    assert np.any(np.isnan(result))
    
    # But not the entire array (with appropriate mode)
    assert not np.all(np.isnan(result))