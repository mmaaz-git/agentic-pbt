#!/usr/bin/env python3
"""
Additional edge case tests for awkward.highlevel to try to find bugs.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np
from hypothesis import given, strategies as st, assume, settings, note
import pytest


# More aggressive strategies
@st.composite
def deeply_nested_arrays(draw):
    """Generate deeply nested arrays to stress test."""
    depth = draw(st.integers(min_value=3, max_value=5))
    
    def gen_nested(d):
        if d == 0:
            return st.integers(min_value=-1000, max_value=1000)
        else:
            # Allow more variation in list sizes, including empty
            return st.lists(gen_nested(d - 1), min_size=0, max_size=5)
    
    data = draw(st.lists(gen_nested(depth - 1), min_size=0, max_size=10))
    return ak.Array(data)


@st.composite
def mixed_type_records(draw):
    """Generate records with mixed types."""
    size = draw(st.integers(min_value=0, max_value=20))
    records = []
    for _ in range(size):
        record = {}
        # Add different field types
        if draw(st.booleans()):
            record["int_field"] = draw(st.integers(-1000, 1000))
        if draw(st.booleans()):
            record["float_field"] = draw(st.floats(allow_nan=False, allow_infinity=False))
        if draw(st.booleans()):
            record["bool_field"] = draw(st.booleans())
        if record:  # Only add non-empty records
            records.append(record)
    
    if records:
        return ak.Array(records)
    else:
        return ak.Array([])


@st.composite
def arrays_with_none(draw):
    """Generate arrays that include None values."""
    base = draw(st.lists(st.one_of(st.none(), st.integers(-100, 100)), min_size=0, max_size=20))
    return ak.Array(base)


# Edge case tests

@given(deeply_nested_arrays())
@settings(max_examples=50)
def test_deeply_nested_flatten(arr):
    """Test flattening deeply nested arrays."""
    # Flatten completely
    fully_flat = ak.flatten(arr, axis=None)
    
    # Check that result is 1D
    assert fully_flat.ndim == 1
    
    # Count total elements manually - this is complex for deep nesting
    # Just check that we got some result without crashing
    assert isinstance(fully_flat, ak.Array)


@given(arrays_with_none())
def test_operations_with_none(arr):
    """Test that operations handle None values correctly."""
    # Test drop_none
    dropped = ak.drop_none(arr)
    assert ak.all(ak.is_none(dropped) == False)
    
    # Test that length after dropping matches non-None count
    none_count = ak.sum(ak.is_none(arr))
    assert len(dropped) == len(arr) - none_count


@given(mixed_type_records())
def test_mixed_record_fields(records):
    """Test handling of records with different field sets."""
    if len(records) == 0:
        return
    
    # Get all fields
    all_fields = records.fields
    
    # Access each field
    for field in all_fields:
        field_data = records[field]
        # Should be able to access without error
        assert isinstance(field_data, ak.Array)


@given(st.lists(st.integers(0, 10), min_size=0, max_size=100))
def test_extreme_slicing(data):
    """Test various slicing edge cases."""
    arr = ak.Array(data)
    
    # Empty slice
    assert len(arr[0:0]) == 0
    
    # Slice beyond bounds
    large_slice = arr[0:1000000]
    assert len(large_slice) == len(arr)
    
    # Negative slice beyond bounds
    if len(arr) > 0:
        assert arr[-1000000] == arr[0]
    
    # Step slicing
    if len(arr) > 1:
        stepped = arr[::2]
        expected_len = (len(arr) + 1) // 2
        assert len(stepped) == expected_len


@given(deeply_nested_arrays())
@settings(max_examples=20)
def test_nested_array_arithmetic(arr):
    """Test arithmetic on deeply nested arrays."""
    # Adding a scalar should preserve structure
    result = arr + 1
    
    # Structure should be preserved
    assert result.ndim == arr.ndim
    assert len(result) == len(arr)


@given(st.lists(st.lists(st.integers(-100, 100), min_size=0, max_size=5), min_size=0, max_size=10))
def test_concatenate_empty_arrays(data):
    """Test concatenating arrays including empty ones."""
    arrays = [ak.Array(sublist) for sublist in data]
    
    if not arrays:
        # Can't concatenate nothing
        return
    
    concatenated = ak.concatenate(arrays)
    
    # Total length should be sum of individual lengths
    expected_len = sum(len(arr) for arr in arrays)
    assert len(concatenated) == expected_len


@given(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def test_mask_all_true_false(data):
    """Test masking with all True or all False masks."""
    arr = ak.Array(data)
    
    # All True mask
    all_true = ak.Array([True] * len(arr))
    masked_true = arr.mask[all_true]
    assert ak.all(ak.is_none(masked_true) == False)
    assert ak.array_equal(masked_true, arr)
    
    # All False mask  
    all_false = ak.Array([False] * len(arr))
    masked_false = arr.mask[all_false]
    assert ak.all(ak.is_none(masked_false) == True)
    assert len(masked_false) == len(arr)


@given(st.lists(st.dictionaries(st.sampled_from(["a", "b", "c"]), st.integers(-100, 100), min_size=1), min_size=1, max_size=10))
def test_zip_unzip_partial_fields(data):
    """Test zip/unzip with records that have different field sets."""
    arr = ak.Array(data)
    
    # Get common fields
    all_fields = set()
    for record in data:
        all_fields.update(record.keys())
    
    if not all_fields:
        return
    
    # Try to unzip
    try:
        unzipped = ak.unzip(arr)
        # Should get a tuple of arrays
        assert isinstance(unzipped, tuple)
    except:
        # Some field configurations might not be unzippable
        pass


@given(st.lists(st.lists(st.integers(-10, 10), min_size=3, max_size=3), min_size=2, max_size=10))
def test_to_numpy_regular_arrays(data):
    """Test to_numpy conversion for perfectly regular arrays."""
    arr = ak.Array(data)
    
    # This should be convertible to numpy
    np_arr = ak.to_numpy(arr)
    
    assert isinstance(np_arr, np.ndarray)
    assert np_arr.shape == (len(data), 3)
    
    # Values should match
    for i in range(len(data)):
        for j in range(3):
            assert np_arr[i, j] == data[i][j]


@given(st.lists(st.integers(-100, 100), min_size=0, max_size=50))
def test_double_masking(data):
    """Test applying mask operation twice."""
    if len(data) < 2:
        return
        
    arr = ak.Array(data)
    
    # First mask
    mask1 = arr > 0
    masked1 = arr.mask[mask1]
    
    # Second mask on already masked array
    mask2 = ak.is_none(masked1) | (masked1 < 50)
    masked2 = masked1.mask[mask2]
    
    # Length should still be preserved
    assert len(masked2) == len(arr)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])