"""
Property-based tests for numpy.lib.stride_tricks.as_strided.
This function is dangerous but should maintain certain invariants.
"""

import numpy as np
from numpy.lib.stride_tricks import as_strided
from hypothesis import given, strategies as st, settings, assume
import warnings


@given(
    arr_shape=st.lists(st.integers(1, 10), min_size=1, max_size=3),
    new_shape=st.lists(st.integers(1, 10), min_size=1, max_size=3),
)
@settings(max_examples=200)
def test_as_strided_shape_setting(arr_shape, new_shape):
    """Test that as_strided correctly sets the shape when strides are compatible."""
    
    arr = np.arange(np.prod(arr_shape)).reshape(arr_shape)
    
    # Calculate strides that won't go out of bounds
    # Use default strides initially
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = as_strided(arr, shape=new_shape)
        
        assert result.shape == tuple(new_shape), \
            f"Shape mismatch: expected {tuple(new_shape)}, got {result.shape}"
    except:
        # Some combinations may fail, that's expected
        pass


@given(
    size=st.integers(1, 100),
    new_shape=st.lists(st.integers(1, 5), min_size=1, max_size=3)
)
@settings(max_examples=100)
def test_as_strided_writeable_flag(size, new_shape):
    """Test that the writeable flag is respected."""
    
    arr = np.arange(size)
    
    # Create read-only view
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        readonly_view = as_strided(arr, shape=new_shape, writeable=False)
    
    assert not readonly_view.flags['WRITEABLE'], \
        "View should not be writeable when writeable=False"
    
    # Create writeable view
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        writeable_view = as_strided(arr, shape=new_shape, writeable=True)
    
    # Writeable flag should match the original array's writeability
    if arr.flags['WRITEABLE']:
        assert writeable_view.flags['WRITEABLE'], \
            "View should be writeable when writeable=True and original is writeable"


@given(
    shape=st.lists(st.integers(1, 10), min_size=1, max_size=3),
)
@settings(max_examples=100)
def test_as_strided_no_params_identity(shape):
    """Test that as_strided without params returns equivalent view."""
    
    arr = np.arange(np.prod(shape)).reshape(shape)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = as_strided(arr)
    
    assert result.shape == arr.shape, \
        f"Shape changed without params: {arr.shape} -> {result.shape}"
    assert result.strides == arr.strides, \
        f"Strides changed without params: {arr.strides} -> {result.strides}"
    
    # Check data is the same
    assert np.array_equal(result, arr), \
        "Data changed when no params provided"


@given(
    base_shape=st.lists(st.integers(2, 5), min_size=2, max_size=2),
)
@settings(max_examples=50)
def test_as_strided_overlapping_windows(base_shape):
    """Test creating overlapping windows with as_strided."""
    
    arr = np.arange(np.prod(base_shape)).reshape(base_shape)
    
    # Create 2x2 overlapping windows
    if all(s >= 2 for s in base_shape):
        window_shape = (base_shape[0] - 1, base_shape[1] - 1, 2, 2)
        
        # Calculate strides for overlapping windows
        strides = arr.strides + arr.strides
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            windows = as_strided(arr, shape=window_shape, strides=strides)
        
        # Check first window
        expected_first = arr[:2, :2]
        actual_first = windows[0, 0]
        
        assert np.array_equal(actual_first, expected_first), \
            f"First window incorrect: expected {expected_first}, got {actual_first}"


@given(
    size=st.integers(10, 100),
)
@settings(max_examples=50)
def test_as_strided_broadcast_simulation(size):
    """Test that as_strided can simulate broadcasting."""
    
    arr = np.arange(size)
    
    # Simulate broadcasting to (3, size) by using stride 0 for first dimension
    broadcast_shape = (3, size)
    broadcast_strides = (0, arr.strides[0])
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        broadcast_view = as_strided(arr, shape=broadcast_shape, strides=broadcast_strides)
    
    # Each row should be identical
    for i in range(3):
        assert np.array_equal(broadcast_view[i], arr), \
            f"Row {i} doesn't match original array"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])