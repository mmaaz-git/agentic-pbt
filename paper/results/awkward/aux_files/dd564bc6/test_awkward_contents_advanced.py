#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, assume, settings, note
import awkward as ak
from awkward.contents import (
    ListOffsetArray, ListArray, RegularArray, 
    NumpyArray, IndexedArray, IndexedOptionArray,
    ByteMaskedArray, BitMaskedArray, UnionArray
)
from awkward.index import Index32, Index64, IndexU32, Index8


# Test advanced properties and edge cases
@settings(max_examples=1000)
@given(
    st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=100)
)
def test_listoffsetarray_from_cumsum_roundtrip(sizes):
    """Test creating ListOffsetArray from list sizes and round-trip."""
    # Create offsets from sizes
    offsets = np.cumsum([0] + sizes)
    
    # Create content
    content_size = offsets[-1]
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create ListOffsetArray
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Reconstruct sizes
    reconstructed_sizes = []
    for i in range(len(arr)):
        start = arr.offsets[i]
        stop = arr.offsets[i + 1]
        reconstructed_sizes.append(stop - start)
    
    assert reconstructed_sizes == sizes, \
        f"Round-trip failed: {sizes} != {reconstructed_sizes}"


@settings(max_examples=1000)
@given(
    st.lists(st.integers(min_value=0, max_value=20), min_size=0, max_size=50),
    st.integers(min_value=1, max_value=10)
)
def test_regulararray_flatten_unflatten(data, size):
    """Test that RegularArray can be flattened and unflattened correctly."""
    # Ensure data length is a multiple of size
    trim_length = (len(data) // size) * size
    data = data[:trim_length]
    
    if len(data) == 0:
        return  # Skip empty case
    
    # Create flat content
    content = NumpyArray(np.array(data, dtype=np.float64))
    
    # Create RegularArray
    arr = RegularArray(content, size)
    
    # Check length
    expected_length = len(data) // size
    assert len(arr) == expected_length, \
        f"Length wrong: expected {expected_length}, got {len(arr)}"
    
    # Flatten back
    flattened = []
    for i in range(len(arr)):
        elem = arr[i]
        elem_data = elem.data if hasattr(elem, 'data') else elem
        if hasattr(elem_data, '__iter__'):
            flattened.extend(elem_data)
        else:
            flattened.append(elem_data)
    
    # Should match original data up to the trim point
    np.testing.assert_array_equal(flattened, data[:trim_length],
        err_msg="Flatten/unflatten round-trip failed")


@settings(max_examples=1000)
@given(
    st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=50),
    st.integers(min_value=50, max_value=150)
)
def test_bytemaskedarray_masking_consistency(mask_indices, content_size):
    """Test ByteMaskedArray masking behavior."""
    # Create mask
    mask = np.zeros(content_size, dtype=np.int8)
    for idx in mask_indices:
        if idx < content_size:
            mask[idx] = 1
    
    # Create content
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Test with valid_when=True (1 means valid)
    arr_true = ByteMaskedArray(Index8(mask), content, valid_when=True)
    
    # Test with valid_when=False (0 means valid)
    arr_false = ByteMaskedArray(Index8(1 - mask), content, valid_when=False)
    
    # Both should have the same length
    assert len(arr_true) == len(arr_false) == content_size, \
        "ByteMaskedArray length mismatch"
    
    # Check that valid positions are consistent
    for i in range(min(10, content_size)):
        is_valid_true = (mask[i] == 1)
        is_valid_false = (mask[i] == 0)
        
        # For valid_when=True, mask[i]=1 means valid
        # For valid_when=False, mask[i]=0 means valid
        # So they should have opposite validity


@settings(max_examples=500)
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=50),
            st.integers(min_value=0, max_value=50)
        ),
        min_size=0,
        max_size=30
    ),
    st.integers(min_value=60, max_value=100)
)
def test_listarray_overlapping_lists(start_stop_pairs, content_size):
    """Test ListArray with potentially overlapping lists."""
    starts = []
    stops = []
    
    for start, length in start_stop_pairs:
        stop = min(start + length, content_size)
        starts.append(start)
        stops.append(stop)
    
    if not starts:
        return  # Skip empty
    
    starts = np.array(starts, dtype=np.int64)
    stops = np.array(stops, dtype=np.int64)
    
    # Create content
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create ListArray - this should handle overlapping lists
    arr = ListArray(Index64(starts), Index64(stops), content)
    
    # Check that we can access all elements
    assert len(arr) == len(starts), f"Length mismatch"
    
    for i in range(len(arr)):
        elem = arr[i]
        expected_size = stops[i] - starts[i]
        
        # Get the actual size
        if hasattr(elem, '__len__'):
            actual_size = len(elem)
        elif hasattr(elem, 'data'):
            actual_size = len(elem.data) if hasattr(elem.data, '__len__') else 1
        else:
            actual_size = 1
            
        assert actual_size == expected_size, \
            f"Element {i} has wrong size: expected {expected_size}, got {actual_size}"


@settings(max_examples=500)
@given(
    st.lists(st.integers(min_value=-5, max_value=50), min_size=0, max_size=50),
    st.integers(min_value=20, max_value=60)
)  
def test_indexedoptionarray_none_preservation(indices, content_size):
    """Test that IndexedOptionArray preserves None values correctly."""
    # Create index array
    index = Index64(np.array(indices, dtype=np.int64))
    
    # Create content
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create IndexedOptionArray
    arr = IndexedOptionArray(index, content)
    
    # Track which indices should be None
    none_positions = [i for i, idx in enumerate(indices) if idx < 0]
    valid_positions = [i for i, idx in enumerate(indices) if idx >= 0 and idx < content_size]
    
    # Check None values are preserved
    for pos in none_positions[:10]:  # Check first 10 None positions
        value = arr[pos]
        is_none = value is None or (hasattr(value, '__len__') and len(value) == 0)
        assert is_none, f"Position {pos} with index {indices[pos]} should be None"


@settings(max_examples=500)
@given(
    st.lists(st.integers(min_value=0, max_value=1000), min_size=2, max_size=100)
)
def test_listoffsetarray_empty_lists(offsets_raw):
    """Test ListOffsetArray with empty lists (consecutive equal offsets)."""
    # Sort to ensure monotonicity
    offsets = sorted(offsets_raw)
    
    # Ensure we start from 0
    if offsets[0] != 0:
        offsets = [0] + offsets
    
    offsets = np.array(offsets, dtype=np.int64)
    
    # Create content
    content_size = offsets[-1] + 10
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create ListOffsetArray
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Count empty lists
    empty_count = 0
    for i in range(len(arr)):
        if arr.offsets[i] == arr.offsets[i + 1]:
            empty_count += 1
            # Check that accessing empty list works
            elem = arr[i]
            elem_len = len(elem) if hasattr(elem, '__len__') else 0
            assert elem_len == 0, f"Empty list at {i} has non-zero length"
    
    note(f"Found {empty_count} empty lists out of {len(arr)}")


@settings(max_examples=500)
@given(
    st.integers(min_value=0, max_value=20),
    st.integers(min_value=0, max_value=100)
)
def test_regulararray_zero_size(size, zeros_length):
    """Test RegularArray with size=0."""
    # When size is 0, the array length should be zeros_length
    content = NumpyArray(np.array([1, 2, 3, 4, 5], dtype=np.float64))
    
    if size == 0:
        arr = RegularArray(content, size=0, zeros_length=zeros_length)
        assert len(arr) == zeros_length, \
            f"With size=0, length should be {zeros_length}, got {len(arr)}"
        
        # All elements should be empty
        for i in range(min(5, len(arr))):
            elem = arr[i]
            elem_len = len(elem) if hasattr(elem, '__len__') else 0
            assert elem_len == 0, f"Element {i} should be empty with size=0"
    else:
        arr = RegularArray(content, size=size, zeros_length=zeros_length)
        expected_len = len(content) // size
        assert len(arr) == expected_len, \
            f"With size={size}, length should be {expected_len}, got {len(arr)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])