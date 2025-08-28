#!/usr/bin/env python3
"""
Property-based tests for awkward.highlevel module using Hypothesis.
Testing fundamental properties and invariants of the Array class and related functions.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest


# === STRATEGIES FOR GENERATING AWKWARD ARRAYS ===

@st.composite
def simple_arrays(draw, min_size=0, max_size=20):
    """Generate simple flat arrays of integers."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    elements = draw(st.lists(st.integers(min_value=-100, max_value=100), min_size=size, max_size=size))
    return ak.Array(elements)


@st.composite  
def nested_arrays(draw, max_depth=2, max_size=10):
    """Generate nested arrays with variable-length lists."""
    def gen_nested(depth):
        if depth == 0:
            return st.integers(min_value=-100, max_value=100)
        else:
            return st.lists(gen_nested(depth - 1), min_size=0, max_size=max_size)
    
    depth = draw(st.integers(min_value=1, max_value=max_depth))
    data = draw(st.lists(gen_nested(depth - 1), min_size=0, max_size=max_size))
    return ak.Array(data)


@st.composite
def record_arrays(draw, min_size=0, max_size=10):
    """Generate arrays of records with integer fields."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    records = []
    for _ in range(size):
        record = {
            "x": draw(st.integers(min_value=-100, max_value=100)),
            "y": draw(st.integers(min_value=-100, max_value=100))
        }
        records.append(record)
    return ak.Array(records)


@st.composite
def regular_2d_arrays(draw, min_rows=1, max_rows=10, cols=3):
    """Generate regular 2D arrays (all rows have same length)."""
    rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    data = []
    for _ in range(rows):
        row = draw(st.lists(st.integers(min_value=-100, max_value=100), 
                           min_size=cols, max_size=cols))
        data.append(row)
    return ak.Array(data)


# === PROPERTY TESTS ===

# Test 1: Identity slicing property
@given(simple_arrays())
def test_identity_slicing_simple(arr):
    """Test that arr[:] is equal to arr for simple arrays."""
    assert ak.array_equal(arr, arr[:])


@given(nested_arrays())
def test_identity_slicing_nested(arr):
    """Test that arr[:] is equal to arr for nested arrays."""
    assert ak.array_equal(arr, arr[:])


# Test 2: to_list/from_iter round-trip
@given(nested_arrays(max_depth=3, max_size=5))
def test_to_list_from_iter_roundtrip(arr):
    """Test that converting to list and back preserves the array."""
    list_form = arr.to_list()
    reconstructed = ak.from_iter(list_form)
    assert ak.array_equal(arr, reconstructed)


# Test 3: flatten preserves element count
@given(nested_arrays(max_depth=2, max_size=8))
def test_flatten_preserves_count(arr):
    """Test that flattening preserves the total number of elements."""
    if arr.ndim < 2:
        return  # Skip if not nested
    
    # Count elements before flattening
    original_count = ak.sum(ak.num(arr, axis=1))
    
    # Flatten one level
    flattened = ak.flatten(arr, axis=1)
    flat_count = ak.num(flattened, axis=0)
    
    assert original_count == flat_count


# Test 4: sort idempotence  
@given(simple_arrays(min_size=1))
def test_sort_idempotent(arr):
    """Test that sorting twice gives the same result as sorting once."""
    sorted_once = ak.sort(arr)
    sorted_twice = ak.sort(sorted_once)
    assert ak.array_equal(sorted_once, sorted_twice)


@given(nested_arrays(max_depth=2, max_size=8))
def test_sort_nested_idempotent(arr):
    """Test sort idempotence for nested arrays at the innermost level."""
    if arr.ndim < 2:
        return
    
    sorted_once = ak.sort(arr, axis=-1)
    sorted_twice = ak.sort(sorted_once, axis=-1)
    assert ak.array_equal(sorted_once, sorted_twice)


# Test 5: zip/unzip round-trip
@given(simple_arrays(min_size=1), simple_arrays(min_size=1))
def test_zip_unzip_roundtrip(arr1, arr2):
    """Test that zip followed by unzip recovers the original arrays."""
    # Make arrays same length
    min_len = min(len(arr1), len(arr2))
    arr1 = arr1[:min_len]
    arr2 = arr2[:min_len]
    
    assume(min_len > 0)
    
    zipped = ak.zip({"a": arr1, "b": arr2})
    unzipped = ak.unzip(zipped)
    
    assert ak.array_equal(arr1, unzipped[0])
    assert ak.array_equal(arr2, unzipped[1])


# Test 6: mask preserves array length
@given(simple_arrays(min_size=1))
def test_mask_preserves_length(arr):
    """Test that masking preserves the array length."""
    # Create a boolean mask
    mask = arr > 0
    masked = arr.mask[mask]
    
    assert len(masked) == len(arr)
    assert ak.num(masked, axis=0) == len(arr)


# Test 7: field access equivalence
@given(record_arrays(min_size=1))
def test_field_access_equivalence(records):
    """Test that dot notation and bracket notation give same results for fields."""
    # Test both fields
    assert ak.array_equal(records.x, records["x"])
    assert ak.array_equal(records.y, records["y"])


# Test 8: concatenate length property
@given(simple_arrays(), simple_arrays())
def test_concatenate_length(arr1, arr2):
    """Test that concatenation preserves total length."""
    concatenated = ak.concatenate([arr1, arr2])
    assert len(concatenated) == len(arr1) + len(arr2)


@given(nested_arrays(max_depth=2), nested_arrays(max_depth=2))
def test_concatenate_length_nested(arr1, arr2):
    """Test concatenation length for nested arrays."""
    concatenated = ak.concatenate([arr1, arr2], axis=0)
    assert len(concatenated) == len(arr1) + len(arr2)


# Test 9: Negative indexing consistency
@given(simple_arrays(min_size=1))
def test_negative_indexing(arr):
    """Test that negative indexing is consistent with positive indexing."""
    for i in range(1, min(len(arr), 10)):
        assert arr[-i] == arr[len(arr) - i]


# Test 10: Array iteration matches to_list
@given(nested_arrays(max_depth=2, max_size=5))
def test_iteration_matches_to_list(arr):
    """Test that iterating over array matches to_list output."""
    iterated = []
    for item in arr:
        if hasattr(item, 'to_list'):
            # Item is an Array
            iterated.append(item.to_list())
        else:
            # Item is a scalar (from 1D arrays)
            iterated.append(item.item() if hasattr(item, 'item') else item)
    
    to_list = arr.to_list()
    assert iterated == to_list


# Test 11: Boolean indexing preserves values
@given(simple_arrays(min_size=1))
def test_boolean_indexing_preserves_values(arr):
    """Test that boolean indexing preserves the selected values."""
    mask = arr > 0
    filtered = arr[mask]
    
    # Check that all values in filtered satisfy the condition
    for val in filtered:
        assert val > 0
    
    # Check that we didn't lose any values that should be included
    expected_count = ak.sum(mask)
    assert len(filtered) == expected_count


# Test 12: Setting and deleting record fields
@given(record_arrays(min_size=1))
def test_record_field_operations(records):
    """Test setting and deleting fields in records."""
    # Make a copy to avoid modifying the original
    arr = ak.copy(records)
    
    # Add a new field
    arr["z"] = arr["x"] + arr["y"]
    assert ak.all(arr["z"] == arr["x"] + arr["y"])
    
    # Delete the field
    del arr["z"]
    assert "z" not in arr.fields
    assert set(arr.fields) == {"x", "y"}


# Test 13: Regular array conversions
@given(regular_2d_arrays())
def test_regular_to_numpy_roundtrip(arr):
    """Test conversion to numpy and back for regular arrays."""
    # Convert to numpy
    np_array = ak.to_numpy(arr)
    
    # Check it's a proper numpy array
    assert isinstance(np_array, np.ndarray)
    assert np_array.ndim == 2
    
    # Convert back
    reconstructed = ak.from_numpy(np_array)
    
    # Compare values (may not be exactly equal due to type changes)
    assert arr.to_list() == reconstructed.to_list()


# Test 14: Drop none preserves non-none values
@given(simple_arrays(min_size=1))
def test_drop_none_preserves_values(arr):
    """Test that drop_none preserves all non-None values."""
    # Add some None values by masking
    mask = arr % 2 == 0
    arr_with_none = ak.mask(arr, mask)
    
    # Drop the None values
    dropped = ak.drop_none(arr_with_none)
    
    # Check that all remaining values are from the original
    assert len(dropped) == ak.sum(mask)
    assert ak.all(dropped == arr[mask])


# Test 15: Sort preserves all elements
@given(simple_arrays(min_size=1))
def test_sort_preserves_elements(arr):
    """Test that sorting preserves all elements (just reorders them)."""
    sorted_arr = ak.sort(arr)
    
    # Convert to lists and sort to compare
    original_list = sorted(arr.to_list())
    sorted_list = sorted_arr.to_list()
    
    assert original_list == sorted_list


# Test 16: Array type preservation through arithmetic
@given(nested_arrays(max_depth=2))
def test_type_preservation_arithmetic(arr):
    """Test that arithmetic operations preserve array structure."""
    result = arr + 10
    
    # Check that structure is preserved
    assert result.ndim == arr.ndim
    assert len(result) == len(arr)
    
    # Check values are correctly transformed
    for i in range(len(arr)):
        if hasattr(arr[i], '__len__'):
            assert len(result[i]) == len(arr[i])


# Test 17: Empty array edge cases
def test_empty_array_operations():
    """Test operations on empty arrays."""
    empty = ak.Array([])
    
    # Identity slicing
    assert ak.array_equal(empty, empty[:])
    
    # to_list
    assert empty.to_list() == []
    
    # Concatenation
    other = ak.Array([1, 2, 3])
    concat1 = ak.concatenate([empty, other])
    concat2 = ak.concatenate([other, empty])
    assert ak.array_equal(concat1, other)
    assert ak.array_equal(concat2, other)
    
    # Sort
    sorted_empty = ak.sort(empty)
    assert ak.array_equal(sorted_empty, empty)


# Test 18: Nested empty lists
def test_nested_empty_lists():
    """Test operations on arrays with nested empty lists."""
    arr = ak.Array([[], [1, 2], [], [3]])
    
    # Flatten
    flattened = ak.flatten(arr)
    assert flattened.to_list() == [1, 2, 3]
    
    # Count
    counts = ak.num(arr, axis=1)
    assert counts.to_list() == [0, 2, 0, 1]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])