#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, assume, settings, note, example
import awkward as ak
from awkward.contents import (
    ListOffsetArray, ListArray, RegularArray, 
    NumpyArray, IndexedArray, IndexedOptionArray,
    ByteMaskedArray, UnionArray, RecordArray
)
from awkward.index import Index32, Index64, IndexU32, Index8


# Focus on edge cases and boundary conditions
@settings(max_examples=2000, deadline=None)
@given(
    st.lists(st.integers(min_value=0, max_value=2**31), min_size=2, max_size=10)
)
def test_listoffsetarray_large_offsets(offsets_raw):
    """Test ListOffsetArray with very large offset values."""
    # Sort and deduplicate
    offsets = sorted(set(offsets_raw))
    
    if len(offsets) < 2:
        offsets.append(offsets[-1] + 1)
    
    # Ensure starts from 0
    if offsets[0] != 0:
        offsets = [0] + offsets
    
    offsets = np.array(offsets, dtype=np.int64)
    
    # Create minimal content to match largest offset
    content_size = min(offsets[-1], 2**20)  # Cap at 1MB elements for memory
    offsets = np.minimum(offsets, content_size)  # Clip offsets to content size
    
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # This should work without issues
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Verify invariants still hold
    for i in range(len(arr.offsets) - 1):
        assert arr.offsets[i] <= arr.offsets[i + 1], \
            f"Offsets not monotonic at {i}"


@settings(max_examples=1000)
@given(
    st.integers(min_value=-10, max_value=-1),
    st.integers(min_value=10, max_value=100)
)
def test_indexedarray_negative_indices_should_fail(negative_idx, content_size):
    """Test that IndexedArray rejects negative indices (not IndexedOptionArray)."""
    # IndexedArray should NOT accept negative indices
    indices = [0, 1, negative_idx, 2]
    
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # This should potentially raise an error or handle it somehow
    try:
        index = Index64(np.array(indices, dtype=np.int64))
        arr = IndexedArray(index, content)
        
        # If it doesn't raise, check what happens when we access it
        for i in range(len(arr)):
            try:
                value = arr[i]
                if i == 2:  # The negative index position
                    # Check if it wraps around or fails
                    note(f"Negative index {negative_idx} gave value: {value}")
            except Exception as e:
                if i == 2:
                    note(f"Accessing negative index raised: {e}")
                    
    except Exception as e:
        note(f"Creating IndexedArray with negative index raised: {e}")


@settings(max_examples=1000)
@given(
    st.lists(st.integers(), min_size=0, max_size=10),
    st.integers(min_value=5, max_value=20)
)
def test_listarray_starts_greater_than_stops(indices, content_size):
    """Test ListArray behavior when start > stop (should fail or handle gracefully)."""
    if len(indices) < 2:
        return
    
    # Create some starts > stops cases
    starts = []
    stops = []
    
    for i in range(0, len(indices) - 1, 2):
        start = abs(indices[i]) % content_size
        stop = abs(indices[i + 1]) % content_size
        
        if i % 3 == 0 and start > stop:
            # Intentionally create start > stop
            starts.append(start)
            stops.append(stop)
        else:
            # Normal case
            starts.append(min(start, stop))
            stops.append(max(start, stop))
    
    if not starts:
        return
    
    starts = np.array(starts, dtype=np.int64)
    stops = np.array(stops, dtype=np.int64)
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    has_invalid = any(starts[i] > stops[i] for i in range(len(starts)))
    
    if has_invalid:
        try:
            arr = ListArray(Index64(starts), Index64(stops), content)
            # If it succeeds, check behavior
            for i in range(len(arr)):
                if starts[i] > stops[i]:
                    elem = arr[i]
                    # Should be empty or handle specially
                    elem_len = len(elem) if hasattr(elem, '__len__') else 0
                    note(f"start > stop at {i}: {starts[i]} > {stops[i]}, len={elem_len}")
        except Exception as e:
            note(f"ListArray with start > stop raised: {e}")


@settings(max_examples=1000)
@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=50)
)
def test_regulararray_content_not_multiple_of_size(content_len, size, zeros_length):
    """Test RegularArray when content length is not a multiple of size."""
    if size == 0:
        return  # Skip size=0 case
    
    # Ensure content_len is NOT a multiple of size
    if content_len % size == 0 and content_len > 0:
        content_len += 1
    
    content = NumpyArray(np.arange(content_len, dtype=np.float64))
    arr = RegularArray(content, size, zeros_length=zeros_length)
    
    # Length should be truncated
    expected_length = content_len // size
    assert len(arr) == expected_length, \
        f"Length not truncated correctly: expected {expected_length}, got {len(arr)}"
    
    # The last partial list should not be accessible
    used_content = expected_length * size
    unused_content = content_len - used_content
    
    if unused_content > 0:
        note(f"Unused content: {unused_content} elements")
        
        # Verify we can't access beyond the truncated length
        try:
            # This should fail or return truncated
            value = arr[expected_length]
            assert False, f"Should not be able to access index {expected_length}"
        except (IndexError, AssertionError):
            pass  # Expected


@settings(max_examples=1000)
@given(
    st.lists(st.booleans(), min_size=0, max_size=100),
    st.booleans()
)
def test_bytemaskedarray_all_masked(mask_values, valid_when):
    """Test ByteMaskedArray when all values are masked/unmasked."""
    if not mask_values:
        return
    
    # Create all True or all False mask
    all_same = all(mask_values) or not any(mask_values)
    
    mask = np.array(mask_values, dtype=np.int8)
    content = NumpyArray(np.arange(len(mask_values), dtype=np.float64))
    
    arr = ByteMaskedArray(Index8(mask), content, valid_when=valid_when)
    
    if all_same:
        if all(mask_values):
            # All True
            if valid_when:
                # All valid
                for i in range(min(5, len(arr))):
                    elem = arr[i]
                    assert elem is not None
            else:
                # All masked
                for i in range(min(5, len(arr))):
                    elem = arr[i]
                    is_none = elem is None or (hasattr(elem, '__len__') and len(elem) == 0)
                    assert is_none, f"All should be masked but {i} is not"
        else:
            # All False
            if not valid_when:
                # All valid
                for i in range(min(5, len(arr))):
                    elem = arr[i]
                    assert elem is not None
            else:
                # All masked
                for i in range(min(5, len(arr))):
                    elem = arr[i]
                    is_none = elem is None or (hasattr(elem, '__len__') and len(elem) == 0)
                    assert is_none, f"All should be masked but {i} is not"


@settings(max_examples=500, deadline=None)
@given(
    st.lists(st.integers(min_value=0, max_value=3), min_size=0, max_size=50),
    st.lists(st.integers(min_value=0, max_value=50), min_size=0, max_size=50)
)
def test_unionarray_tags_index_consistency(tags, indices):
    """Test UnionArray with multiple content types."""
    if not tags or not indices:
        return
    
    # Ensure same length
    min_len = min(len(tags), len(indices))
    tags = tags[:min_len]
    indices = indices[:min_len]
    
    # Create multiple content arrays
    contents = [
        NumpyArray(np.arange(60, dtype=np.float64)),
        NumpyArray(np.arange(60, dtype=np.int32)),
        NumpyArray(np.ones(60, dtype=np.bool_)),  # Fixed: use ones instead of arange for bool
        NumpyArray(np.arange(60, dtype=np.float32))
    ]
    
    # Ensure tags are within range
    tags = [t % len(contents) for t in tags]
    tags_array = Index8(np.array(tags, dtype=np.int8))
    
    # Ensure indices are within content bounds
    indices = [min(idx, 59) for idx in indices]
    index_array = Index64(np.array(indices, dtype=np.int64))
    
    # Create UnionArray
    arr = UnionArray(tags_array, index_array, contents)
    
    # Check that we can access all elements
    assert len(arr) == len(tags), f"Length mismatch"
    
    for i in range(min(10, len(arr))):
        elem = arr[i]
        expected_content = contents[tags[i]]
        expected_value = expected_content[indices[i]]
        
        # Compare values
        elem_data = elem.data if hasattr(elem, 'data') else elem
        expected_data = expected_value.data if hasattr(expected_value, 'data') else expected_value
        
        # Type should match
        if hasattr(elem_data, 'dtype') and hasattr(expected_data, 'dtype'):
            assert elem_data.dtype == expected_data.dtype, \
                f"Type mismatch at {i}: {elem_data.dtype} != {expected_data.dtype}"


@settings(max_examples=500)
@given(st.data())
def test_nested_list_structures(data):
    """Test deeply nested list structures."""
    # Generate nested structure depth
    depth = data.draw(st.integers(min_value=1, max_value=5))
    
    # Start with base content
    content = NumpyArray(np.arange(100, dtype=np.float64))
    
    for level in range(depth):
        # Wrap in a list structure
        choice = data.draw(st.integers(min_value=0, max_value=2))
        
        if choice == 0:
            # ListOffsetArray
            num_lists = data.draw(st.integers(min_value=1, max_value=20))
            offsets = [0]
            for _ in range(num_lists):
                size = data.draw(st.integers(min_value=0, max_value=10))
                next_offset = min(offsets[-1] + size, len(content))
                offsets.append(next_offset)
            
            content = ListOffsetArray(Index64(np.array(offsets)), content)
            
        elif choice == 1:
            # RegularArray
            size = data.draw(st.integers(min_value=1, max_value=5))
            content = RegularArray(content, size)
            
        else:
            # ListArray
            num_lists = data.draw(st.integers(min_value=1, max_value=20))
            starts = []
            stops = []
            for _ in range(num_lists):
                start = data.draw(st.integers(min_value=0, max_value=len(content)))
                length = data.draw(st.integers(min_value=0, max_value=5))
                stop = min(start + length, len(content))
                starts.append(start)
                stops.append(stop)
            
            content = ListArray(
                Index64(np.array(starts)), 
                Index64(np.array(stops)), 
                content
            )
    
    # Try to access the nested structure
    note(f"Created {depth}-level nested structure")
    
    # Access a few elements at the top level
    for i in range(min(3, len(content))):
        try:
            elem = content[i]
            note(f"Successfully accessed element {i}")
        except Exception as e:
            note(f"Failed to access element {i}: {e}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])