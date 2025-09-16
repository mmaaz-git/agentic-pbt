#!/usr/bin/env python3
"""
More aggressive property tests to find bugs.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test for specific edge cases and properties

@given(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def test_argsort_indices_valid(data):
    """Test that argsort returns valid indices."""
    arr = ak.Array(data)
    indices = ak.argsort(arr)
    
    # All indices should be in valid range
    assert ak.all(indices >= 0)
    assert ak.all(indices < len(arr))
    
    # Indices should be unique
    assert len(set(indices.to_list())) == len(indices)
    
    # Using these indices should give sorted array
    sorted_via_indices = arr[indices]
    sorted_direct = ak.sort(arr)
    assert ak.array_equal(sorted_via_indices, sorted_direct)


@given(st.lists(st.lists(st.integers(-100, 100), min_size=0, max_size=5), min_size=1, max_size=10))
def test_num_axis_parameter(data):
    """Test ak.num with different axis parameters."""
    arr = ak.Array(data)
    
    # axis=0 should give total length
    num_axis0 = ak.num(arr, axis=0)
    assert num_axis0 == len(arr)
    
    # axis=1 should give lengths of sublists
    num_axis1 = ak.num(arr, axis=1)
    expected = [len(sublist) for sublist in data]
    assert num_axis1.to_list() == expected


@given(st.lists(st.integers(-100, 100), min_size=2, max_size=20))
def test_argmax_argmin_consistency(data):
    """Test that argmax and argmin return consistent results."""
    arr = ak.Array(data)
    
    max_idx = ak.argmax(arr)
    min_idx = ak.argmin(arr)
    
    # The values at these indices should be max and min
    assert arr[max_idx] == ak.max(arr)
    assert arr[min_idx] == ak.min(arr)
    
    # Indices should be different unless all values are the same
    if ak.min(arr) != ak.max(arr):
        assert max_idx != min_idx


@given(st.lists(st.lists(st.integers(-10, 10), min_size=0, max_size=3), min_size=0, max_size=5))
def test_flatten_axis_none(data):
    """Test that flatten with axis=None completely flattens."""
    arr = ak.Array(data)
    
    flat = ak.flatten(arr, axis=None)
    
    # Should be 1D
    assert flat.ndim == 1
    
    # Should contain all elements
    expected_elements = []
    for sublist in data:
        expected_elements.extend(sublist)
    
    assert flat.to_list() == expected_elements


@given(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def test_fill_none_with_scalar(data):
    """Test fill_none operation."""
    arr = ak.Array(data)
    
    # Add some None values
    mask = arr % 3 == 0
    arr_with_none = ak.mask(arr, ~mask)
    
    # Fill with a value
    filled = ak.fill_none(arr_with_none, -999)
    
    # Check no None remain
    assert not ak.any(ak.is_none(filled))
    
    # Check filled values
    for i in range(len(arr)):
        if data[i] % 3 == 0:
            assert filled[i] == -999
        else:
            assert filled[i] == data[i]


@given(st.lists(st.dictionaries(st.sampled_from(["x", "y"]), st.integers(-100, 100), min_size=2, max_size=2), min_size=1, max_size=10))
def test_with_field_operation(data):
    """Test adding fields to records."""
    arr = ak.Array(data)
    
    # Add a new field
    arr_with_z = ak.with_field(arr, arr.x + arr.y, "z")
    
    # Check the new field exists and has correct values
    assert "z" in arr_with_z.fields
    assert ak.all(arr_with_z.z == arr_with_z.x + arr_with_z.y)
    
    # Original should be unchanged (immutable)
    assert "z" not in arr.fields


@given(st.lists(st.integers(0, 100), min_size=1, max_size=20))
def test_unique_operation(data):
    """Test unique-like operations if they exist."""
    arr = ak.Array(data)
    
    # Check if values are preserved through conversions
    unique_vals = set(data)
    arr_vals = set(arr.to_list())
    
    assert unique_vals == arr_vals


@given(st.lists(st.lists(st.integers(-10, 10), min_size=1, max_size=3), min_size=2, max_size=5))
def test_broadcast_arrays(data):
    """Test broadcasting behavior."""
    arr1 = ak.Array(data)
    arr2 = ak.Array([100])  # Single element to broadcast
    
    # Try to broadcast
    broadcasted = ak.broadcast_arrays(arr1, arr2)
    
    # First should be unchanged
    assert ak.array_equal(broadcasted[0], arr1)
    
    # Second should be broadcasted to match structure
    assert len(broadcasted[1]) == len(arr1)


@given(st.lists(st.integers(-100, 100), min_size=1, max_size=20))
def test_ones_like_zeros_like(data):
    """Test ones_like and zeros_like operations."""
    arr = ak.Array(data)
    
    ones = ak.ones_like(arr)
    zeros = ak.zeros_like(arr)
    
    # Check structure is preserved
    assert len(ones) == len(arr)
    assert len(zeros) == len(arr)
    
    # Check values
    assert ak.all(ones == 1)
    assert ak.all(zeros == 0)


@given(st.lists(st.lists(st.integers(-100, 100), min_size=0, max_size=5), min_size=0, max_size=10))
def test_pad_none_operation(data):
    """Test pad_none to ensure arrays have minimum length."""
    arr = ak.Array(data)
    
    # Pad to length 3 on axis 1
    padded = ak.pad_none(arr, 3, axis=1)
    
    # Check all sublists have at least length 3
    for item in padded:
        assert len(item) >= 3
        
    # Original values should be preserved
    for i, sublist in enumerate(data):
        for j, val in enumerate(sublist):
            assert padded[i][j] == val


@given(st.lists(st.integers(1, 100), min_size=2, max_size=10))
def test_run_lengths(data):
    """Test run_lengths for consecutive equal values."""
    # Create array with runs
    arr_data = []
    for val in data[:3]:  # Use only first 3 to avoid huge arrays
        arr_data.extend([val] * val)  # Create runs of length equal to value
    
    if not arr_data:
        return
        
    arr = ak.Array(arr_data)
    runs = ak.run_lengths(arr)
    
    # Check that we can reconstruct the original
    reconstructed = []
    for i in range(len(runs)):
        value = arr[ak.sum(runs[:i])] if i > 0 else arr[0]
        reconstructed.extend([value] * runs[i])
    
    assert reconstructed == arr_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])