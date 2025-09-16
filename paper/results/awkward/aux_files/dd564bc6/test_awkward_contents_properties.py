#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, assume, settings
import awkward as ak
from awkward.contents import (
    ListOffsetArray, ListArray, RegularArray, 
    NumpyArray, IndexedArray, IndexedOptionArray
)
from awkward.index import Index32, Index64, IndexU32


# Helper strategies for generating valid indices
@st.composite
def valid_offsets(draw):
    """Generate valid offsets for ListOffsetArray."""
    size = draw(st.integers(min_value=0, max_value=100))
    
    # Generate increasing offsets starting from 0
    if size == 0:
        return np.array([0], dtype=np.int64)
    
    # Generate deltas and cumsum to ensure monotonicity
    deltas = draw(st.lists(st.integers(min_value=0, max_value=10), min_size=size, max_size=size))
    offsets = np.cumsum([0] + deltas, dtype=np.int64)
    return offsets


@st.composite
def valid_starts_stops(draw):
    """Generate valid starts and stops for ListArray."""
    size = draw(st.integers(min_value=0, max_value=50))
    max_content_len = draw(st.integers(min_value=100, max_value=200))
    
    starts = []
    stops = []
    
    for _ in range(size):
        start = draw(st.integers(min_value=0, max_value=max_content_len))
        # Ensure stop >= start
        stop = draw(st.integers(min_value=start, max_value=max_content_len))
        starts.append(start)
        stops.append(stop)
    
    return np.array(starts, dtype=np.int64), np.array(stops, dtype=np.int64), max_content_len


# Test 1: ListOffsetArray offsets monotonicity property
@given(valid_offsets())
def test_listoffsetarray_offsets_monotonic(offsets):
    """Test that ListOffsetArray maintains offset monotonicity."""
    # Create content that's large enough
    content_size = offsets[-1] if len(offsets) > 0 else 0
    content = NumpyArray(np.arange(content_size + 10, dtype=np.float64))
    
    # Create the array
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Check that offsets are monotonic
    retrieved_offsets = arr.offsets.data
    for i in range(len(retrieved_offsets) - 1):
        assert retrieved_offsets[i] <= retrieved_offsets[i + 1], \
            f"Offsets not monotonic at index {i}: {retrieved_offsets[i]} > {retrieved_offsets[i + 1]}"
    
    # Check that length is correct
    assert len(arr) == len(offsets) - 1, \
        f"Length mismatch: expected {len(offsets) - 1}, got {len(arr)}"


# Test 2: ListArray starts <= stops invariant
@given(valid_starts_stops())
def test_listarray_starts_stops_invariant(starts_stops_max):
    """Test that ListArray maintains starts <= stops invariant."""
    starts, stops, max_content_len = starts_stops_max
    
    # Create content
    content = NumpyArray(np.arange(max_content_len + 10, dtype=np.float64))
    
    # Create the array
    arr = ListArray(Index64(starts), Index64(stops), content)
    
    # Check the invariant
    retrieved_starts = arr.starts.data
    retrieved_stops = arr.stops.data
    
    for i in range(len(retrieved_starts)):
        assert retrieved_starts[i] <= retrieved_stops[i], \
            f"Invariant violated at index {i}: start {retrieved_starts[i]} > stop {retrieved_stops[i]}"
    
    # Check length
    assert len(arr) == len(starts), f"Length mismatch: expected {len(starts)}, got {len(arr)}"


# Test 3: RegularArray length calculation property
@given(
    size=st.integers(min_value=0, max_value=20),
    content_length=st.integers(min_value=0, max_value=200),
    zeros_length=st.integers(min_value=0, max_value=50)
)
def test_regulararray_length_calculation(size, content_length, zeros_length):
    """Test that RegularArray correctly calculates its length."""
    # Create content
    content = NumpyArray(np.arange(content_length, dtype=np.float64))
    
    # Create the array
    arr = RegularArray(content, size, zeros_length=zeros_length)
    
    # Check the length calculation
    if size > 0:
        expected_length = content_length // size
    else:
        expected_length = zeros_length
    
    assert len(arr) == expected_length, \
        f"Length calculation wrong: expected {expected_length}, got {len(arr)}"


# Test 4: ListOffsetArray to ListArray conversion invariant
@given(valid_offsets())
def test_listoffsetarray_to_listarray_conversion(offsets):
    """Test that ListOffsetArray starts/stops properties are consistent."""
    # Create content
    content_size = offsets[-1] if len(offsets) > 0 else 0
    content = NumpyArray(np.arange(content_size + 10, dtype=np.float64))
    
    # Create ListOffsetArray
    offset_arr = ListOffsetArray(Index64(offsets), content)
    
    # Check that starts and stops are derived correctly
    if len(offsets) > 1:
        starts = offset_arr.starts.data
        stops = offset_arr.stops.data
        
        # starts should be offsets[:-1]
        np.testing.assert_array_equal(starts, offsets[:-1], 
            err_msg="starts != offsets[:-1]")
        
        # stops should be offsets[1:]
        np.testing.assert_array_equal(stops, offsets[1:],
            err_msg="stops != offsets[1:]")
        
        # Create equivalent ListArray
        list_arr = ListArray(Index64(starts), Index64(stops), content)
        
        # They should have the same length
        assert len(offset_arr) == len(list_arr), \
            f"Length mismatch between ListOffsetArray ({len(offset_arr)}) and ListArray ({len(list_arr)})"
        
        # Check element-wise equivalence for a few elements
        for i in range(min(5, len(offset_arr))):
            offset_elem = offset_arr[i]
            list_elem = list_arr[i]
            # Convert to numpy arrays for comparison
            offset_data = np.asarray(offset_elem.data) if hasattr(offset_elem, 'data') else offset_elem
            list_data = np.asarray(list_elem.data) if hasattr(list_elem, 'data') else list_elem
            np.testing.assert_array_equal(offset_data, list_data,
                err_msg=f"Element {i} differs between ListOffsetArray and ListArray")


# Test 5: IndexedArray index bounds property
@given(
    st.lists(st.integers(min_value=-1, max_value=20), min_size=0, max_size=50),
    st.integers(min_value=10, max_value=30)
)
def test_indexedarray_index_bounds(indices, content_size):
    """Test that IndexedArray respects index bounds."""
    # Filter out negative indices for regular IndexedArray
    valid_indices = [i for i in indices if i >= 0]
    
    if not valid_indices:
        return  # Skip if no valid indices
    
    # Ensure indices are within content bounds
    valid_indices = [min(i, content_size - 1) for i in valid_indices]
    
    index = Index64(np.array(valid_indices, dtype=np.int64))
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create IndexedArray
    arr = IndexedArray(index, content)
    
    # Check that length matches index length
    assert len(arr) == len(valid_indices), \
        f"Length mismatch: expected {len(valid_indices)}, got {len(arr)}"
    
    # Check that all indexed values are accessible
    for i in range(len(arr)):
        value = arr[i]
        expected = content[valid_indices[i]]
        # Extract the actual data values
        value_data = value.data if hasattr(value, 'data') else value
        expected_data = expected.data if hasattr(expected, 'data') else expected
        assert value_data == expected_data, \
            f"Indexed value at {i} doesn't match: {value_data} != {expected_data}"


# Test 6: IndexedOptionArray with negative indices
@given(
    st.lists(st.integers(min_value=-5, max_value=20), min_size=0, max_size=50),
    st.integers(min_value=10, max_value=30)
)
def test_indexedoptionarray_negative_indices(indices, content_size):
    """Test that IndexedOptionArray treats negative indices as None."""
    # Ensure non-negative indices are within bounds
    bounded_indices = []
    for i in indices:
        if i < 0:
            bounded_indices.append(i)  # Keep negative as-is
        else:
            bounded_indices.append(min(i, content_size - 1))
    
    index = Index64(np.array(bounded_indices, dtype=np.int64))
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create IndexedOptionArray
    arr = IndexedOptionArray(index, content)
    
    # Check length
    assert len(arr) == len(bounded_indices), \
        f"Length mismatch: expected {len(bounded_indices)}, got {len(arr)}"
    
    # Check that negative indices produce None
    for i, idx in enumerate(bounded_indices):
        value = arr[i]
        if idx < 0:
            # Should be None/masked
            assert value is None or len(value) == 0, \
                f"Negative index {idx} at position {i} didn't produce None"
        else:
            # Should have the content value
            expected = content[idx]
            if value is not None:
                # Extract the actual data values
                value_data = value.data if hasattr(value, 'data') else value
                expected_data = expected.data if hasattr(expected, 'data') else expected
                assert value_data == expected_data, \
                    f"Value at {i} doesn't match: {value_data} != {expected_data}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])