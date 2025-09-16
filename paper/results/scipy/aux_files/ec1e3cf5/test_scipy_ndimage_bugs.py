"""Focused tests to find real bugs in scipy.ndimage"""

import numpy as np
import scipy.ndimage as ndi
from hypothesis import given, strategies as st, assume, settings
import pytest
import math

# More sophisticated array strategies
@st.composite
def small_float_arrays(draw, min_dims=2, max_dims=3):
    """Generate small float arrays with controlled values"""
    shape = draw(st.lists(st.integers(min_value=2, max_value=8), 
                          min_size=min_dims, max_size=max_dims))
    size = int(np.prod(shape))
    data = draw(st.lists(st.floats(min_value=-10, max_value=10,
                                   allow_nan=False, allow_infinity=False,
                                   width=32),
                        min_size=size, max_size=size))
    return np.array(data).reshape(shape)

@st.composite  
def valid_zoom_factors(draw, ndim):
    """Generate valid zoom factors"""
    # Generate zoom factors that are reasonable (not too extreme)
    if draw(st.booleans()):
        # Single zoom factor for all dimensions
        return draw(st.floats(min_value=0.5, max_value=2.0, allow_nan=False))
    else:
        # Different zoom factor per dimension
        return draw(st.lists(st.floats(min_value=0.5, max_value=2.0, allow_nan=False),
                            min_size=ndim, max_size=ndim))

# Test 1: Zoom with grid_mode consistency
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=200)
def test_zoom_grid_mode_consistency(arr):
    """Zooming by 1 should preserve array regardless of grid_mode"""
    zoom_normal = ndi.zoom(arr, 1, grid_mode=False)
    zoom_grid = ndi.zoom(arr, 1, grid_mode=True)
    
    # Both should equal the original when zoom=1
    assert np.allclose(arr, zoom_normal, rtol=1e-10, atol=1e-10)
    assert np.allclose(arr, zoom_grid, rtol=1e-10, atol=1e-10)

# Test 2: Spline order consistency
@given(small_float_arrays(min_dims=1, max_dims=1))
@settings(max_examples=200)
def test_spline_order_consistency(arr):
    """Order 0 (nearest neighbor) should give same result for integer shifts"""
    # Shift by integer amount with different orders
    shift_amount = 2
    
    shifted_0 = ndi.shift(arr, shift_amount, order=0, mode='constant')
    shifted_1 = ndi.shift(arr, shift_amount, order=1, mode='constant')
    
    # For integer shifts, order shouldn't matter for the shifted values
    # (though boundary handling might differ)
    valid_indices_0 = shifted_0 != 0
    valid_indices_1 = shifted_1 != 0
    
    if np.any(valid_indices_0) and np.any(valid_indices_1):
        # Where both have valid values, they should be similar
        both_valid = valid_indices_0 & valid_indices_1
        if np.any(both_valid):
            assert np.allclose(shifted_0[both_valid], shifted_1[both_valid], rtol=0.1)

# Test 3: Gaussian filter separability
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_gaussian_filter_separability(arr):
    """2D Gaussian filter should equal successive 1D filters"""
    sigma = 1.0
    
    # 2D filter
    filtered_2d = ndi.gaussian_filter(arr, sigma=sigma)
    
    # Equivalent as two 1D filters
    filtered_x = ndi.gaussian_filter1d(arr, sigma=sigma, axis=0)
    filtered_xy = ndi.gaussian_filter1d(filtered_x, sigma=sigma, axis=1)
    
    assert np.allclose(filtered_2d, filtered_xy, rtol=1e-10, atol=1e-10)

# Test 4: Convolve commutativity for symmetric kernels
@given(st.lists(st.floats(min_value=-5, max_value=5, allow_nan=False),
                min_size=3, max_size=7))
@settings(max_examples=200)
def test_convolve_symmetric_kernel(data):
    """Convolution with symmetric kernel should be commutative with correlation"""
    arr = np.array(data)
    
    # Create a symmetric kernel
    kernel = np.array([1, 2, 1])
    
    convolved = ndi.convolve1d(arr, kernel, mode='constant')
    correlated = ndi.correlate1d(arr, kernel, mode='constant')
    
    # For symmetric kernels, convolution equals correlation
    assert np.allclose(convolved, correlated, rtol=1e-10, atol=1e-10)

# Test 5: Distance transform monotonicity
@given(st.integers(min_value=5, max_value=15),
       st.integers(min_value=5, max_value=15))
@settings(max_examples=100)
def test_distance_transform_monotonic(h, w):
    """Distance transform should be monotonic from boundaries"""
    # Create array with single point in center
    arr = np.zeros((h, w), dtype=bool)
    arr[h//2, w//2] = True
    
    dist = ndi.distance_transform_edt(arr)
    
    # Distance should be maximum at the center
    center_dist = dist[h//2, w//2]
    assert center_dist == np.max(dist)
    
    # Check monotonicity along axes
    # Moving away from center should decrease distance
    center_row = dist[h//2, :]
    center_col = dist[:, w//2]
    
    # Check that distance decreases as we move away from center
    for i in range(1, w//2):
        if w//2 + i < w:
            assert center_row[w//2] >= center_row[w//2 + i]
        if w//2 - i >= 0:
            assert center_row[w//2] >= center_row[w//2 - i]

# Test 6: Map coordinates with identity mapping
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_map_coordinates_identity(arr):
    """map_coordinates with identity coordinates should preserve array"""
    # Create identity coordinate mapping
    coords = np.mgrid[:arr.shape[0], :arr.shape[1]]
    coords = coords.reshape(2, -1)
    
    # Map coordinates with identity mapping
    result = ndi.map_coordinates(arr, coords, order=1)
    result = result.reshape(arr.shape)
    
    assert np.allclose(arr, result, rtol=1e-10, atol=1e-10)

# Test 7: Percentile filter edge cases
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_percentile_filter_bounds(arr):
    """Percentile filter with 0 and 100 should equal min and max filters"""
    size = 3
    
    # Skip if array too small
    if arr.shape[0] < size or arr.shape[1] < size:
        return
    
    percentile_0 = ndi.percentile_filter(arr, 0, size=size)
    min_filter = ndi.minimum_filter(arr, size=size)
    assert np.allclose(percentile_0, min_filter, rtol=1e-10, atol=1e-10)
    
    percentile_100 = ndi.percentile_filter(arr, 100, size=size)
    max_filter = ndi.maximum_filter(arr, size=size)
    assert np.allclose(percentile_100, max_filter, rtol=1e-10, atol=1e-10)

# Test 8: Fourier shift linearity
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=50)
def test_fourier_shift_linearity(arr):
    """Fourier shift should be additive: shift(x, a+b) = shift(shift(x, a), b)"""
    shift_a = [0.5, 0.5]
    shift_b = [0.3, 0.3]
    shift_total = [0.8, 0.8]
    
    # Single shift
    shifted_total = ndi.fourier_shift(arr, shift_total)
    
    # Two successive shifts
    shifted_a = ndi.fourier_shift(arr, shift_a)
    shifted_ab = ndi.fourier_shift(shifted_a, shift_b)
    
    # Should be equivalent (within numerical precision)
    assert np.allclose(np.real(shifted_total), np.real(shifted_ab), rtol=1e-5, atol=1e-5)

# Test 9: Sobel filter antisymmetry
@given(small_float_arrays(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_sobel_antisymmetry(arr):
    """Sobel filter on negative image should give negative of Sobel on original"""
    sobel_pos = ndi.sobel(arr)
    sobel_neg = ndi.sobel(-arr)
    
    # Sobel of negative should equal negative of Sobel
    assert np.allclose(sobel_pos, -sobel_neg, rtol=1e-10, atol=1e-10)

# Test 10: Generic filter with identity function
@given(small_float_arrays(min_dims=1, max_dims=1))
@settings(max_examples=50)
def test_generic_filter_identity(arr):
    """Generic filter with identity function should preserve array values"""
    # Skip if array too small
    if len(arr) < 3:
        return
        
    # Function that returns the center value (identity for size=1)
    def identity(buffer):
        return buffer[len(buffer)//2]
    
    result = ndi.generic_filter(arr, identity, size=3, mode='constant')
    
    # Interior values should be preserved
    if len(arr) > 2:
        assert np.allclose(arr[1:-1], result[1:-1], rtol=1e-10, atol=1e-10)