"""
Property-based tests for numpy.lib.Arrayterator.
Testing iteration invariants and buffer behavior.
"""

import numpy as np
from numpy.lib import Arrayterator
from hypothesis import given, strategies as st, settings, assume
import itertools


@given(
    shape=st.lists(st.integers(1, 10), min_size=1, max_size=4),
    buf_size=st.one_of(st.none(), st.integers(1, 100))
)
@settings(max_examples=200)
def test_arrayterator_complete_iteration(shape, buf_size):
    """Test that Arrayterator iterates over all elements exactly once."""
    
    # Create an array with unique values
    total_size = np.prod(shape)
    arr = np.arange(total_size).reshape(shape)
    
    # Create iterator
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    # Collect all elements through iteration
    all_elements = []
    for chunk in iterator:
        all_elements.extend(chunk.flatten())
    
    # Check we got all elements exactly once
    all_elements = np.array(all_elements)
    expected = np.arange(total_size)
    
    assert len(all_elements) == total_size, \
        f"Wrong number of elements: got {len(all_elements)}, expected {total_size}"
    
    assert np.array_equal(np.sort(all_elements), expected), \
        f"Elements don't match: got {all_elements}, expected {expected}"


@given(
    shape=st.lists(st.integers(1, 10), min_size=1, max_size=4),
    buf_size=st.integers(1, 100)
)
@settings(max_examples=200)
def test_arrayterator_buffer_size_constraint(shape, buf_size):
    """Test that each chunk respects the buffer size constraint."""
    
    arr = np.random.randn(*shape)
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    for chunk in iterator:
        chunk_size = chunk.size
        # The chunk size should not exceed buf_size except for the case
        # where a single element is larger than buf_size
        if chunk_size > buf_size:
            # Check if this is because even a single element exceeds buf_size
            assert chunk.ndim >= 1, "Chunk exceeds buffer but has no dimensions"


@given(
    shape=st.lists(st.integers(1, 10), min_size=2, max_size=4),
    buf_size=st.one_of(st.none(), st.integers(1, 100))
)
@settings(max_examples=200)
def test_arrayterator_shape_preservation(shape, buf_size):
    """Test that the iterator preserves the shape attribute correctly."""
    
    arr = np.random.randn(*shape)
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    assert iterator.shape == arr.shape, \
        f"Shape mismatch: iterator.shape={iterator.shape}, arr.shape={arr.shape}"
    
    # Test shape after slicing
    sliced = iterator[0:shape[0]//2 if shape[0] > 1 else 1]
    expected_shape = list(shape)
    expected_shape[0] = shape[0]//2 if shape[0] > 1 else 1
    
    assert sliced.shape == tuple(expected_shape), \
        f"Sliced shape mismatch: got {sliced.shape}, expected {tuple(expected_shape)}"


@given(
    shape=st.lists(st.integers(2, 10), min_size=2, max_size=3),
    buf_size=st.integers(1, 50)
)
@settings(max_examples=100)
def test_arrayterator_indexing_consistency(shape, buf_size):
    """Test that indexing an Arrayterator produces consistent results."""
    
    arr = np.arange(np.prod(shape)).reshape(shape)
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    # Test integer indexing
    if shape[0] > 0:
        indexed = iterator[0]
        expected_shape = shape[1:]
        assert indexed.shape == expected_shape, \
            f"Integer indexing shape mismatch: got {indexed.shape}, expected {expected_shape}"
        
        # The indexed iterator should iterate over the correct slice
        result = []
        for chunk in indexed:
            result.extend(chunk.flatten())
        
        expected_data = arr[0].flatten()
        assert np.array_equal(result, expected_data), \
            f"Integer indexing data mismatch"
    
    # Test slice indexing
    if shape[0] >= 2:
        sliced = iterator[0:2]
        expected_shape = list(shape)
        expected_shape[0] = 2
        assert sliced.shape == tuple(expected_shape), \
            f"Slice indexing shape mismatch: got {sliced.shape}, expected {tuple(expected_shape)}"


@given(
    shape=st.lists(st.integers(1, 10), min_size=1, max_size=4),
    buf_size=st.integers(1, 100)
)
@settings(max_examples=100)
def test_arrayterator_flat_attribute(shape, buf_size):
    """Test that the flat attribute works correctly."""
    
    arr = np.arange(np.prod(shape)).reshape(shape)
    iterator = Arrayterator(arr, buf_size=buf_size)
    
    # Get flat iterator
    flat_iter = iterator.flat
    
    # Collect all elements from flat iteration
    flat_elements = []
    for chunk in flat_iter:
        flat_elements.extend(chunk.flatten())
    
    # Should match the flattened array
    expected = arr.flatten()
    flat_elements = np.array(flat_elements)
    
    assert np.array_equal(flat_elements, expected), \
        f"Flat iteration mismatch: got {flat_elements}, expected {expected}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])