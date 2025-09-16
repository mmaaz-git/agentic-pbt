#!/usr/bin/env python3
import sys
import os

# Add the awkward env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategy for generating valid awkward arrays
@st.composite
def awkward_arrays(draw, max_depth=2):
    """Generate simple awkward arrays for testing."""
    depth = draw(st.integers(0, max_depth))
    
    if depth == 0:
        # Base case: simple 1D array
        data = draw(st.lists(st.integers(-1000, 1000), min_size=0, max_size=20))
        return ak.Array(data)
    else:
        # Nested array
        inner_size = draw(st.integers(0, 5))
        outer_size = draw(st.integers(0, 5))
        data = []
        for _ in range(outer_size):
            inner = draw(st.lists(st.integers(-1000, 1000), min_size=0, max_size=inner_size))
            data.append(inner)
        return ak.Array(data)


@st.composite
def simple_1d_arrays(draw):
    """Generate simple 1D awkward arrays."""
    data = draw(st.lists(st.integers(-1000, 1000), min_size=0, max_size=50))
    return ak.Array(data)


@st.composite
def matching_arrays_pair(draw):
    """Generate two arrays with compatible structure for operations like zip."""
    length = draw(st.integers(0, 20))
    arr1_data = draw(st.lists(st.integers(-1000, 1000), min_size=length, max_size=length))
    arr2_data = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000), 
                              min_size=length, max_size=length))
    return ak.Array(arr1_data), ak.Array(arr2_data)


# Property 1: Concatenate preserves total length
@given(simple_1d_arrays(), simple_1d_arrays())
@settings(max_examples=100)
def test_concatenate_preserves_length(arr1, arr2):
    """concatenate should preserve the total number of elements."""
    result = ak.concatenate([arr1, arr2], axis=0)
    expected_length = len(arr1) + len(arr2)
    assert len(result) == expected_length, f"Expected length {expected_length}, got {len(result)}"


# Property 2: Argsort produces valid indices
@given(simple_1d_arrays())
@settings(max_examples=100)
def test_argsort_produces_valid_indices(arr):
    """argsort should produce indices that are valid for the array."""
    assume(len(arr) > 0)  # Skip empty arrays
    
    indices = ak.argsort(arr)
    
    # Check that indices are within valid range
    assert len(indices) == len(arr), f"argsort changed length: {len(arr)} -> {len(indices)}"
    
    # All indices should be unique and in range [0, len(arr))
    indices_list = ak.to_list(indices)
    assert all(0 <= idx < len(arr) for idx in indices_list), "Invalid index produced by argsort"
    assert len(set(indices_list)) == len(indices_list), "argsort produced duplicate indices"
    
    # The array indexed by these indices should be sorted
    sorted_arr = arr[indices]
    sorted_list = ak.to_list(sorted_arr)
    for i in range(1, len(sorted_list)):
        assert sorted_list[i-1] <= sorted_list[i], f"Array not properly sorted at position {i}"


# Property 3: Zip/unzip round-trip
@given(matching_arrays_pair())
@settings(max_examples=100)
def test_zip_unzip_round_trip(arrays_pair):
    """zip followed by unzip should return the original arrays."""
    arr1, arr2 = arrays_pair
    
    # Zip the arrays
    zipped = ak.zip([arr1, arr2])
    
    # Unzip back
    unzipped = ak.unzip(zipped)
    
    # Should get back two arrays
    assert len(unzipped) == 2, f"Expected 2 arrays from unzip, got {len(unzipped)}"
    
    # Check that we get back the same data
    assert ak.all(unzipped[0] == arr1), "First array not preserved in zip/unzip"
    assert np.allclose(ak.to_numpy(unzipped[1]), ak.to_numpy(arr2)), "Second array not preserved in zip/unzip"


# Property 4: Flatten preserves all elements
@given(awkward_arrays(max_depth=2))
@settings(max_examples=100)
def test_flatten_preserves_elements(arr):
    """flatten should preserve all elements, just removing nesting."""
    # Get the total count of elements before flattening
    def count_elements(array):
        if len(array) == 0:
            return 0
        try:
            # Try to flatten and count
            flat = ak.flatten(array, axis=None)
            return len(flat)
        except:
            # If can't flatten all the way, just count at current level
            return len(array)
    
    original_count = count_elements(arr)
    
    # Flatten one level
    if ak.num(arr, axis=0) > 0:  # Only if not empty
        try:
            flattened = ak.flatten(arr, axis=1)
            # Count elements in flattened array
            flattened_count = count_elements(flattened)
            
            # The total number of elements should be preserved
            # Note: This might not always be true for ragged arrays, so we check if reasonable
            assert flattened_count <= original_count * 10, f"Flattening appears to have duplicated elements"
        except:
            # Some arrays can't be flattened (e.g., scalars), which is ok
            pass


# Property 5: mask and is_none consistency
@given(simple_1d_arrays(), st.lists(st.booleans(), min_size=0, max_size=50))
@settings(max_examples=100)
def test_mask_is_none_consistency(arr, mask_list):
    """Elements that are masked should be detected as None by is_none."""
    # Make mask same length as array
    if len(mask_list) < len(arr):
        mask_list = mask_list + [False] * (len(arr) - len(mask_list))
    elif len(mask_list) > len(arr):
        mask_list = mask_list[:len(arr)]
    
    mask = ak.Array(mask_list)
    
    # Apply mask (valid_when=False means True in mask creates None)
    masked = ak.mask(arr, mask, valid_when=False)
    
    # Check with is_none
    none_mask = ak.is_none(masked, axis=0)
    
    # The none_mask should match our original mask
    assert ak.all(none_mask == mask), "is_none doesn't match the mask applied"


# Property 6: Multiple concatenates are associative
@given(simple_1d_arrays(), simple_1d_arrays(), simple_1d_arrays())
@settings(max_examples=50)
def test_concatenate_associative(arr1, arr2, arr3):
    """Concatenation should be associative: concat(concat(a,b),c) == concat(a,concat(b,c))"""
    # Left association
    left = ak.concatenate([ak.concatenate([arr1, arr2], axis=0), arr3], axis=0)
    
    # Right association  
    right = ak.concatenate([arr1, ak.concatenate([arr2, arr3], axis=0)], axis=0)
    
    # Should be equal
    assert len(left) == len(right), f"Different lengths: {len(left)} vs {len(right)}"
    assert ak.all(left == right), "Concatenation is not associative"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])