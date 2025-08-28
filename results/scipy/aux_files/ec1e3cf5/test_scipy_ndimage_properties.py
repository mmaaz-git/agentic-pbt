"""Property-based tests for scipy.ndimage using Hypothesis"""

import numpy as np
import scipy.ndimage as ndi
from hypothesis import given, strategies as st, assume, settings
import pytest
import warnings

# Strategies for generating arrays
def array_strategy(min_dims=1, max_dims=4, dtype=np.float64):
    """Generate random numpy arrays"""
    shape = st.lists(st.integers(min_value=2, max_value=10), 
                     min_size=min_dims, max_size=max_dims)
    return shape.flatmap(lambda s: st.builds(
        lambda data: np.array(data).reshape(s),
        st.lists(st.floats(min_value=-100, max_value=100, 
                          allow_nan=False, allow_infinity=False),
                min_size=int(np.prod(s)), max_size=int(np.prod(s)))
    ).map(lambda arr: arr.astype(dtype)))

def binary_array_strategy(min_dims=2, max_dims=2):
    """Generate random binary arrays"""
    shape = st.lists(st.integers(min_value=3, max_value=20), 
                     min_size=min_dims, max_size=max_dims)
    return shape.flatmap(lambda s: st.builds(
        lambda data: np.array(data).reshape(s),
        st.lists(st.booleans(), min_size=int(np.prod(s)), max_size=int(np.prod(s)))
    ))

# Test 1: Identity transformations
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_shift_identity(arr):
    """shift(x, 0) should equal x"""
    result = ndi.shift(arr, shift=[0] * arr.ndim, mode='constant')
    assert np.allclose(arr, result, rtol=1e-10, atol=1e-10)

@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_zoom_identity(arr):
    """zoom(x, 1) should equal x"""
    result = ndi.zoom(arr, zoom=1, mode='constant')
    assert np.allclose(arr, result, rtol=1e-10, atol=1e-10)

@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_rotate_identity(arr):
    """rotate(x, 0) should equal x"""
    result = ndi.rotate(arr, angle=0, reshape=False, mode='constant')
    assert np.allclose(arr, result, rtol=1e-10, atol=1e-10)

# Test 2: Rotation cycles
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=50)
def test_rotate_360_cycle(arr):
    """rotate(x, 360) should equal x"""
    result = ndi.rotate(arr, angle=360, reshape=False, mode='constant', order=1)
    # More tolerance needed due to interpolation errors
    assert np.allclose(arr, result, rtol=1e-2, atol=1e-2)

@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=50)
def test_rotate_180_twice(arr):
    """rotate(rotate(x, 180), 180) should equal x"""
    rotated_once = ndi.rotate(arr, angle=180, reshape=False, mode='constant', order=1)
    rotated_twice = ndi.rotate(rotated_once, angle=180, reshape=False, mode='constant', order=1)
    assert np.allclose(arr, rotated_twice, rtol=1e-2, atol=1e-2)

# Test 3: Morphological idempotence
@given(binary_array_strategy())
@settings(max_examples=100)
def test_binary_opening_idempotent(binary_arr):
    """opening(opening(x)) = opening(x)"""
    opened_once = ndi.binary_opening(binary_arr)
    opened_twice = ndi.binary_opening(opened_once)
    assert np.array_equal(opened_once, opened_twice)

@given(binary_array_strategy())
@settings(max_examples=100)
def test_binary_closing_idempotent(binary_arr):
    """closing(closing(x)) = closing(x)"""
    closed_once = ndi.binary_closing(binary_arr)
    closed_twice = ndi.binary_closing(closed_once)
    assert np.array_equal(closed_once, closed_twice)

# Test 4: Morphological duality
@given(binary_array_strategy())
@settings(max_examples=100)
def test_erosion_dilation_duality(binary_arr):
    """erosion(X) = complement(dilation(complement(X)))"""
    # Direct erosion
    eroded = ndi.binary_erosion(binary_arr)
    
    # Dual operation
    complement = ~binary_arr
    dilated_complement = ndi.binary_dilation(complement)
    dual_result = ~dilated_complement
    
    assert np.array_equal(eroded, dual_result)

# Test 5: Filter properties
@given(array_strategy(min_dims=2, max_dims=3))
@settings(max_examples=100)
def test_median_filter_identity(arr):
    """median_filter(x, size=1) = x"""
    result = ndi.median_filter(arr, size=1)
    assert np.allclose(arr, result)

@given(array_strategy(min_dims=2, max_dims=3))
@settings(max_examples=100)
def test_filter_preserves_shape(arr):
    """Filters should preserve array shape"""
    # Test various filters
    gaussian = ndi.gaussian_filter(arr, sigma=1)
    assert gaussian.shape == arr.shape
    
    uniform = ndi.uniform_filter(arr, size=3)
    assert uniform.shape == arr.shape
    
    if arr.ndim <= 2:  # median_filter has limitations for high dims
        median = ndi.median_filter(arr, size=3)
        assert median.shape == arr.shape

# Test 6: Distance transform properties
@given(binary_array_strategy())
@settings(max_examples=100)
def test_distance_transform_boundary(binary_arr):
    """Distance transform is 0 at boundaries (False values)"""
    dist = ndi.distance_transform_edt(binary_arr)
    
    # All False positions should have distance 0
    assert np.all(dist[~binary_arr] == 0)
    
    # All True positions should have distance > 0 (if any exist)
    if np.any(binary_arr):
        assert np.all(dist[binary_arr] > 0)

# Test 7: Convolution with identity kernel
@given(st.lists(st.floats(min_value=-100, max_value=100, 
                          allow_nan=False, allow_infinity=False),
                min_size=5, max_size=20))
@settings(max_examples=100)
def test_convolve1d_identity(data):
    """convolve1d with [0,1,0] kernel should preserve array"""
    arr = np.array(data)
    identity_kernel = np.array([0, 1, 0])
    result = ndi.convolve1d(arr, identity_kernel, mode='constant')
    assert np.allclose(arr, result)

# Test 8: Label consistency
@given(binary_array_strategy())
@settings(max_examples=100)
def test_label_find_objects_consistency(binary_arr):
    """Number of labels should match number of objects found"""
    labeled, num_features = ndi.label(binary_arr)
    
    if num_features > 0:
        objects = ndi.find_objects(labeled)
        assert objects is not None
        assert len(objects) == num_features
        
        # Each object should be a valid slice
        for obj in objects:
            assert obj is not None
            for slice_dim in obj:
                assert isinstance(slice_dim, slice)

# Test 9: Shift inverse property
@given(array_strategy(min_dims=2, max_dims=2),
       st.lists(st.floats(min_value=-5, max_value=5, allow_nan=False),
                min_size=2, max_size=2))
@settings(max_examples=50)
def test_shift_inverse(arr, shift_vals):
    """shift(shift(x, s), -s) should approximately equal x"""
    shift = np.array(shift_vals[:arr.ndim])
    
    shifted = ndi.shift(arr, shift, mode='constant', order=1)
    shifted_back = ndi.shift(shifted, -shift, mode='constant', order=1)
    
    # Due to interpolation at boundaries, we need some tolerance
    # and we focus on the center region
    if arr.shape[0] > 4 and arr.shape[1] > 4:
        center = arr[2:-2, 2:-2]
        center_result = shifted_back[2:-2, 2:-2]
        assert np.allclose(center, center_result, rtol=1e-2, atol=1e-2)

# Test 10: Maximum and minimum filter ordering
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_max_min_filter_ordering(arr):
    """maximum_filter result >= original >= minimum_filter result"""
    size = 3
    max_filtered = ndi.maximum_filter(arr, size=size)
    min_filtered = ndi.minimum_filter(arr, size=size)
    
    # The maximum filter should be >= original array
    assert np.all(max_filtered >= arr - 1e-10)
    
    # The minimum filter should be <= original array
    assert np.all(min_filtered <= arr + 1e-10)
    
    # max should be >= min
    assert np.all(max_filtered >= min_filtered - 1e-10)

# Test 11: Gaussian filter with sigma=0
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_gaussian_filter_zero_sigma(arr):
    """gaussian_filter with sigma=0 should preserve array"""
    result = ndi.gaussian_filter(arr, sigma=0)
    assert np.allclose(arr, result)

# Test 12: Binary operations on empty arrays
@given(binary_array_strategy())
@settings(max_examples=100) 
def test_binary_operations_empty(binary_arr):
    """Binary operations on all-False arrays should return all-False"""
    assume(not np.any(binary_arr))  # Only test all-False arrays
    
    eroded = ndi.binary_erosion(binary_arr)
    assert not np.any(eroded)
    
    dilated = ndi.binary_dilation(binary_arr)
    assert not np.any(dilated)
    
    opened = ndi.binary_opening(binary_arr)
    assert not np.any(opened)
    
    closed = ndi.binary_closing(binary_arr)
    assert not np.any(closed)

# Test 13: Rank filter edge cases
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=100)
def test_rank_filter_extremes(arr):
    """rank_filter with rank 0 = minimum_filter, rank -1 = maximum_filter"""
    size = 3
    
    # Rank 0 should give minimum
    rank_0 = ndi.rank_filter(arr, rank=0, size=size)
    min_filter = ndi.minimum_filter(arr, size=size)
    assert np.allclose(rank_0, min_filter)
    
    # Rank -1 should give maximum
    rank_max = ndi.rank_filter(arr, rank=-1, size=size)
    max_filter = ndi.maximum_filter(arr, size=size)
    assert np.allclose(rank_max, max_filter)

# Test 14: Affine transform identity
@given(array_strategy(min_dims=2, max_dims=2))
@settings(max_examples=50)
def test_affine_transform_identity(arr):
    """Affine transform with identity matrix should preserve array"""
    identity_matrix = np.eye(arr.ndim)
    result = ndi.affine_transform(arr, identity_matrix, mode='constant', order=1)
    assert np.allclose(arr, result, rtol=1e-2, atol=1e-2)

# Test 15: Grey morphology idempotence
@given(array_strategy(min_dims=2, max_dims=2, dtype=np.uint8))
@settings(max_examples=50)
def test_grey_opening_closing_idempotent(arr):
    """Grey opening and closing should be idempotent"""
    # Ensure array is in valid range for grey morphology
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    
    # Test opening idempotence
    opened_once = ndi.grey_opening(arr, size=3)
    opened_twice = ndi.grey_opening(opened_once, size=3)
    assert np.allclose(opened_once, opened_twice)
    
    # Test closing idempotence
    closed_once = ndi.grey_closing(arr, size=3)
    closed_twice = ndi.grey_closing(closed_once, size=3)
    assert np.allclose(closed_once, closed_twice)