"""Property-based tests for scipy.ndimage using Hypothesis."""

import numpy as np
import scipy.ndimage as ndi
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Strategy for generating small binary arrays
@st.composite
def binary_arrays(draw, min_dim=2, max_dim=4, min_size=3, max_size=10):
    """Generate random binary arrays for morphological operations."""
    ndim = draw(st.integers(min_value=min_dim, max_value=max_dim))
    shape = tuple(draw(st.integers(min_value=min_size, max_value=max_size)) for _ in range(ndim))
    array = draw(st.builds(
        lambda s: np.random.randint(0, 2, size=s, dtype=bool),
        st.just(shape)
    ))
    return array


# Strategy for generating small float arrays
@st.composite  
def float_arrays(draw, min_dim=1, max_dim=3, min_size=2, max_size=8):
    """Generate random float arrays for filter and transform operations."""
    ndim = draw(st.integers(min_value=min_dim, max_value=max_dim))
    shape = tuple(draw(st.integers(min_value=min_size, max_value=max_size)) for _ in range(ndim))
    
    # Generate finite float values
    flat_size = int(np.prod(shape))  # Convert to Python int for Hypothesis
    values = draw(st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=flat_size,
        max_size=flat_size
    ))
    return np.array(values).reshape(shape)


# Test 1: Morphological opening idempotence
@given(binary_arrays())
@settings(max_examples=100)
def test_opening_idempotence(arr):
    """Opening an already opened image should not change it."""
    opened_once = ndi.binary_opening(arr)
    opened_twice = ndi.binary_opening(opened_once)
    assert np.array_equal(opened_once, opened_twice), \
        "Opening should be idempotent but second application changed the result"


# Test 2: Opening = erosion then dilation
@given(binary_arrays())
@settings(max_examples=100)
def test_opening_composition(arr):
    """binary_opening should equal erosion followed by dilation."""
    opened = ndi.binary_opening(arr)
    eroded_then_dilated = ndi.binary_dilation(ndi.binary_erosion(arr))
    assert np.array_equal(opened, eroded_then_dilated), \
        "Opening should equal erosion followed by dilation"


# Test 3: Closing = dilation then erosion
@given(binary_arrays())
@settings(max_examples=100)
def test_closing_composition(arr):
    """binary_closing should equal dilation followed by erosion."""
    closed = ndi.binary_closing(arr)
    dilated_then_eroded = ndi.binary_erosion(ndi.binary_dilation(arr))
    assert np.array_equal(closed, dilated_then_eroded), \
        "Closing should equal dilation followed by erosion"


# Test 4: Identity transforms
@given(float_arrays(min_dim=2, max_dim=2))
@settings(max_examples=100)
def test_shift_identity(arr):
    """Shifting by 0 should preserve the array."""
    shifted = ndi.shift(arr, shift=[0, 0], order=1)
    assert np.allclose(arr, shifted, rtol=1e-10), \
        "Shift by 0 should preserve the array"


@given(float_arrays(min_dim=2, max_dim=2))
@settings(max_examples=100)
def test_rotate_identity(arr):
    """Rotating by 0 degrees should preserve the array."""
    rotated = ndi.rotate(arr, angle=0, reshape=False, order=1)
    assert np.allclose(arr, rotated, rtol=1e-10), \
        "Rotate by 0 degrees should preserve the array"


@given(float_arrays(min_dim=2, max_dim=2))
@settings(max_examples=100)
def test_zoom_identity(arr):
    """Zooming by factor 1 should preserve the array."""
    zoomed = ndi.zoom(arr, zoom=1, order=1)
    assert np.allclose(arr, zoomed, rtol=1e-10), \
        "Zoom by factor 1 should preserve the array"


# Test 5: Median filter with size 1
@given(float_arrays())
@settings(max_examples=100)
def test_median_filter_size_1(arr):
    """Median filter with size 1 should be identity operation."""
    filtered = ndi.median_filter(arr, size=1)
    assert np.allclose(arr, filtered, rtol=1e-10), \
        "Median filter with size 1 should preserve the array"


# Test 6: Center of mass bounds
@given(float_arrays(min_dim=2, max_dim=2))
@settings(max_examples=100)
def test_center_of_mass_bounds(arr):
    """Center of mass should be within array bounds for non-negative arrays."""
    # Make array non-negative
    arr = np.abs(arr)
    assume(np.sum(arr) > 0)  # Need non-zero mass
    
    com = ndi.center_of_mass(arr)
    
    # Check bounds
    for i, coord in enumerate(com):
        assert 0 <= coord < arr.shape[i], \
            f"Center of mass coordinate {coord} at dimension {i} is outside bounds [0, {arr.shape[i]})"


# Test 7: Label function produces unique labels
@given(binary_arrays(min_size=4, max_size=15))
@settings(max_examples=100)
def test_label_uniqueness(arr):
    """Each connected component should get a unique label."""
    labeled, num_features = ndi.label(arr)
    
    # Get all unique labels (excluding background 0)
    unique_labels = np.unique(labeled[labeled > 0])
    
    # Should have consecutive labels from 1 to num_features
    if num_features > 0:
        expected_labels = np.arange(1, num_features + 1)
        assert np.array_equal(unique_labels, expected_labels), \
            f"Labels should be consecutive from 1 to {num_features}, got {unique_labels}"


# Test 8: Erosion removes more than dilation
@given(binary_arrays())
@settings(max_examples=100)
def test_erosion_dilation_relationship(arr):
    """Erosion should remove pixels, dilation should add pixels."""
    eroded = ndi.binary_erosion(arr)
    dilated = ndi.binary_dilation(arr)
    
    # Count true pixels
    original_count = np.sum(arr)
    eroded_count = np.sum(eroded)
    dilated_count = np.sum(dilated)
    
    # Erosion should not increase pixels
    assert eroded_count <= original_count, \
        f"Erosion increased pixel count from {original_count} to {eroded_count}"
    
    # Dilation should not decrease pixels
    assert dilated_count >= original_count, \
        f"Dilation decreased pixel count from {original_count} to {dilated_count}"


# Test 9: Double erosion vs erosion with iterations=2
@given(binary_arrays())
@settings(max_examples=100)
def test_erosion_iterations(arr):
    """Double erosion should equal erosion with iterations=2."""
    double_eroded = ndi.binary_erosion(ndi.binary_erosion(arr))
    iter2_eroded = ndi.binary_erosion(arr, iterations=2)
    assert np.array_equal(double_eroded, iter2_eroded), \
        "Double erosion should equal erosion with iterations=2"


# Test 10: Shift inverse property
@given(
    float_arrays(min_dim=2, max_dim=2, min_size=5, max_size=10),
    st.floats(min_value=-3, max_value=3, allow_nan=False)
)
@settings(max_examples=100)
def test_shift_inverse(arr, shift_amount):
    """Shifting by x then -x should approximately restore original."""
    # Use constant mode to avoid boundary effects
    shifted_forward = ndi.shift(arr, shift=[shift_amount, 0], order=1, mode='constant', cval=0)
    shifted_back = ndi.shift(shifted_forward, shift=[-shift_amount, 0], order=1, mode='constant', cval=0)
    
    # Check only the interior region to avoid boundary effects
    if abs(shift_amount) < 1:
        # For small shifts, can check most of the array
        assert np.allclose(arr[1:-1, 1:-1], shifted_back[1:-1, 1:-1], rtol=1e-5, atol=1e-5), \
            "Shift inverse property failed"


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])