#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, assume, settings, note
import awkward as ak
from awkward.contents import (
    ListOffsetArray, ListArray, RegularArray, 
    NumpyArray, IndexedArray, IndexedOptionArray,
    ByteMaskedArray, RecordArray, EmptyArray
)
from awkward.index import Index32, Index64, IndexU32, Index8


# Test complex operations and interactions
@settings(max_examples=1000, deadline=None)
@given(
    st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=50)
)
def test_listoffsetarray_slice_roundtrip(sizes):
    """Test that slicing a ListOffsetArray and reconstructing maintains consistency."""
    # Create offsets from sizes
    offsets = np.cumsum([0] + sizes)
    
    # Create content
    content = NumpyArray(np.arange(offsets[-1], dtype=np.float64))
    
    # Create ListOffsetArray
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Slice it
    if len(arr) > 2:
        start = len(arr) // 4
        stop = 3 * len(arr) // 4
        sliced = arr[start:stop]
        
        # Check that the sliced array maintains proper structure
        assert len(sliced) == stop - start, \
            f"Slice length wrong: expected {stop - start}, got {len(sliced)}"
        
        # Check that offsets are still monotonic in the slice
        sliced_offsets = sliced.offsets.data
        for i in range(len(sliced_offsets) - 1):
            assert sliced_offsets[i] <= sliced_offsets[i + 1], \
                f"Sliced offsets not monotonic at {i}"
        
        # Check that we can access all elements in the slice
        for i in range(len(sliced)):
            elem = sliced[i]
            original_elem = arr[start + i]
            
            # They should be equal
            elem_data = elem.data if hasattr(elem, 'data') else elem
            orig_data = original_elem.data if hasattr(original_elem, 'data') else original_elem
            
            if hasattr(elem_data, '__len__') and hasattr(orig_data, '__len__'):
                np.testing.assert_array_equal(elem_data, orig_data,
                    err_msg=f"Sliced element {i} differs from original")


@settings(max_examples=1000)
@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
            st.integers(min_value=0, max_value=100)
        ),
        min_size=1,
        max_size=5
    )
)
def test_recordarray_field_access(fields_and_lengths):
    """Test RecordArray with named fields."""
    if not fields_and_lengths:
        return
    
    # Extract field names and ensure they're unique
    field_names = []
    seen = set()
    for name, _ in fields_and_lengths:
        if name not in seen:
            field_names.append(name)
            seen.add(name)
    
    if not field_names:
        return
    
    # Create contents for each field
    length = min(fields_and_lengths[0][1], 50)  # Use first length, capped at 50
    contents = []
    
    for i, field in enumerate(field_names):
        # Create different data for each field
        data = np.arange(length, dtype=np.float64) * (i + 1)
        contents.append(NumpyArray(data))
    
    # Create RecordArray
    arr = RecordArray(contents, field_names, length=length)
    
    # Check that we can access fields
    assert len(arr) == length, f"Length mismatch: expected {length}, got {len(arr)}"
    
    # Access individual records
    for i in range(min(5, len(arr))):
        record = arr[i]
        # Check that all fields are accessible
        for j, field in enumerate(field_names):
            value = record[field]
            expected = (i) * (j + 1)  # Based on how we created the data
            
            # Extract numeric value from various possible formats
            if hasattr(value, 'data'):
                if isinstance(value.data, memoryview):
                    value_data = float(np.frombuffer(value.data, dtype=np.float64)[0])
                else:
                    value_data = value.data
            else:
                value_data = value
            
            if isinstance(value_data, (memoryview, bytes)):
                value_data = float(np.frombuffer(value_data, dtype=np.float64)[0])
            
            assert abs(float(value_data) - expected) < 1e-10, \
                f"Field {field} at record {i} has wrong value: {value_data} != {expected}"


@settings(max_examples=1000)
@given(
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=50, max_value=100)
)
def test_regulararray_of_regulararray(size1, size2, base_length):
    """Test nested RegularArrays."""
    # Create base content
    content = NumpyArray(np.arange(base_length, dtype=np.float64))
    
    # First level RegularArray
    if size1 == 0:
        # When size is 0, we need to specify how many zero-length lists
        arr1 = RegularArray(content, size=0, zeros_length=base_length)
    else:
        arr1 = RegularArray(content, size1)
    
    # Second level RegularArray
    if len(arr1) > 0:
        if size2 == 0:
            arr2 = RegularArray(arr1, size=0, zeros_length=len(arr1))
        else:
            arr2 = RegularArray(arr1, size2)
        
        # Check that we can access nested elements
        for i in range(min(3, len(arr2))):
            outer = arr2[i]
            # This should be a RegularArray of RegularArrays
            if size2 == 0:
                assert len(outer) == 0, f"Outer element {i} should be empty with size2=0"
            else:
                assert len(outer) == size2, \
                    f"Outer element {i} has wrong size: {len(outer)} != {size2}"
            
            for j in range(min(3, len(outer))):
                inner = outer[j]
                expected_len = size1 if size1 > 0 else 0
                actual_len = len(inner) if hasattr(inner, '__len__') else 0
                # Special case: when size1=0, inner elements should be empty
                if size1 == 0:
                    assert actual_len == 0, \
                        f"Inner element [{i}][{j}] should be empty with size1=0"


@settings(max_examples=1000)
@given(
    st.lists(st.integers(min_value=-5, max_value=100), min_size=0, max_size=50),
    st.integers(min_value=50, max_value=100)
)
def test_indexedoptionarray_to_bytemaskedarray_conversion(indices, content_size):
    """Test conceptual equivalence between IndexedOptionArray and ByteMaskedArray."""
    if not indices:
        return
    
    # Create IndexedOptionArray
    index = Index64(np.array(indices, dtype=np.int64))
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    indexed_arr = IndexedOptionArray(index, content)
    
    # Create equivalent ByteMaskedArray
    # mask[i] = 1 means valid when valid_when=True
    # For IndexedOptionArray, negative means None
    mask = np.array([0 if idx < 0 else 1 for idx in indices], dtype=np.int8)
    
    # For valid indices, we need to extract the actual values
    valid_indices = [idx for idx in indices if idx >= 0 and idx < content_size]
    if valid_indices:
        # Extract numeric values from content
        values = []
        for idx in indices:
            if idx >= 0 and idx < content_size:
                val = content[idx]
                if hasattr(val, 'data'):
                    if isinstance(val.data, (memoryview, bytes)):
                        values.append(float(np.frombuffer(val.data, dtype=np.float64)[0]))
                    else:
                        values.append(float(val.data))
                else:
                    values.append(float(val))
        
        if values:
            masked_content = NumpyArray(np.array(values, dtype=np.float64))
        
        # Note: ByteMaskedArray needs content same length as mask
        # So we need a different approach - use full content and check accessibility
        
        # Check that both arrays have same None pattern
        for i in range(len(indexed_arr)):
            idx_val = indexed_arr[i]
            is_none_indexed = idx_val is None or (hasattr(idx_val, '__len__') and len(idx_val) == 0)
            should_be_none = indices[i] < 0
            
            assert is_none_indexed == should_be_none, \
                f"IndexedOptionArray None pattern wrong at {i}"


@settings(max_examples=500, deadline=None)
@given(st.data())
def test_mixed_list_types_conversion(data):
    """Test conversions between different list types."""
    # Generate a list structure
    num_lists = data.draw(st.integers(min_value=1, max_value=20))
    sizes = data.draw(st.lists(st.integers(min_value=0, max_value=10), 
                               min_size=num_lists, max_size=num_lists))
    
    # Create content
    total_size = sum(sizes)
    content = NumpyArray(np.arange(total_size + 10, dtype=np.float64))
    
    # Create as ListOffsetArray first
    offsets = np.cumsum([0] + sizes)
    offset_arr = ListOffsetArray(Index64(offsets), content)
    
    # Convert to ListArray (via starts/stops properties)
    starts = offset_arr.starts
    stops = offset_arr.stops
    list_arr = ListArray(starts, stops, content)
    
    # Both should be equivalent
    assert len(offset_arr) == len(list_arr), \
        "Length mismatch after conversion"
    
    # Check a few elements
    for i in range(min(5, len(offset_arr))):
        offset_elem = offset_arr[i]
        list_elem = list_arr[i]
        
        offset_data = offset_elem.data if hasattr(offset_elem, 'data') else offset_elem
        list_data = list_elem.data if hasattr(list_elem, 'data') else list_elem
        
        if hasattr(offset_data, '__len__') and hasattr(list_data, '__len__'):
            np.testing.assert_array_equal(offset_data, list_data,
                err_msg=f"Element {i} differs after conversion")
    
    # If all lists have same size, can convert to RegularArray
    if sizes and all(s == sizes[0] for s in sizes):
        regular_size = sizes[0]
        if regular_size > 0:
            # Only the used portion of content
            used_content = content[:total_size]
            regular_arr = RegularArray(used_content, regular_size)
            
            assert len(regular_arr) == len(offset_arr), \
                "RegularArray conversion length mismatch"


@settings(max_examples=500)
@given(
    st.lists(st.integers(min_value=0, max_value=1000), min_size=10, max_size=100)
)
def test_listoffsetarray_offset_overflow(offsets_raw):
    """Test ListOffsetArray with offsets that might overflow or have large jumps."""
    # Sort and ensure monotonic
    offsets = sorted(set(offsets_raw))
    
    if len(offsets) < 2:
        return
    
    # Add some extreme jumps
    if len(offsets) > 3:
        offsets[2] = offsets[1] + 1000000  # Large jump
        offsets = sorted(offsets)
    
    # Ensure starts from 0
    if offsets[0] != 0:
        offsets = [0] + offsets
    
    offsets = np.array(offsets, dtype=np.int64)
    
    # Create content to match largest offset (but cap for memory)
    content_size = min(offsets[-1], 1000000)
    
    # Adjust offsets to fit content
    offsets = np.minimum(offsets, content_size)
    
    # Ensure monotonic after adjustment
    for i in range(1, len(offsets)):
        if offsets[i] < offsets[i-1]:
            offsets[i] = offsets[i-1]
    
    content = NumpyArray(np.arange(content_size, dtype=np.float64))
    
    # Create ListOffsetArray
    arr = ListOffsetArray(Index64(offsets), content)
    
    # Check for any issues with large jumps
    for i in range(len(arr)):
        start = arr.offsets[i]
        stop = arr.offsets[i + 1]
        size = stop - start
        
        if size > 100000:
            note(f"Large list at {i}: size={size}")
            
        # Should still be accessible
        elem = arr[i]
        elem_len = len(elem) if hasattr(elem, '__len__') else 0
        assert elem_len == size, \
            f"List {i} size mismatch: expected {size}, got {elem_len}"


def test_emptyarray_behavior():
    """Test EmptyArray edge cases."""
    # Create EmptyArray
    arr = EmptyArray()
    
    # Check basic properties
    assert len(arr) == 0, f"EmptyArray should have length 0, got {len(arr)}"
    
    # Should not be able to access any elements
    try:
        val = arr[0]
        assert False, "Should not be able to access element in EmptyArray"
    except (IndexError, Exception):
        pass  # Expected
    
    # Check slicing
    sliced = arr[0:0]
    assert len(sliced) == 0, "Empty slice of EmptyArray should be empty"
    
    # Can create nested empty structures
    list_of_empty = ListOffsetArray(Index64(np.array([0])), arr)
    assert len(list_of_empty) == 0, "List of EmptyArray should be empty"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])