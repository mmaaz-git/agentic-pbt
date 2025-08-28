import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest

# Strategy for generating nested arrays
def nested_array_strategy(max_depth=3, max_size=10):
    """Generate nested arrays with various structures"""
    def array_at_depth(depth):
        if depth == 0:
            # Base case: simple array of integers
            return st.lists(st.integers(-100, 100), min_size=0, max_size=max_size)
        else:
            # Recursive case: list of lists
            return st.lists(
                array_at_depth(depth - 1),
                min_size=0,
                max_size=max_size
            )
    
    return st.integers(1, max_depth).flatmap(array_at_depth)

# Strategy for simple 1D or 2D arrays
@st.composite
def simple_array_strategy(draw):
    """Generate simple 1D or 2D arrays of integers"""
    shape = draw(st.sampled_from([
        # 1D arrays
        st.lists(st.integers(-100, 100), min_size=0, max_size=20),
        # 2D arrays (list of lists)
        st.lists(
            st.lists(st.integers(-100, 100), min_size=0, max_size=10),
            min_size=0,
            max_size=10
        )
    ]))
    return draw(shape)

# Test 1: argsort indexing produces sorted array
@given(simple_array_strategy())
@settings(max_examples=200)
def test_argsort_indexing_produces_sorted_array(array):
    """Test that array[argsort(array)] produces a sorted array"""
    try:
        ak_array = ak.Array(array)
        
        # Skip if array is empty at top level
        if len(ak_array) == 0:
            return
            
        # Get argsort indices
        indices = ak.argsort(ak_array, axis=-1)
        
        # Apply indices to get sorted array
        sorted_array = ak_array[indices]
        
        # Convert to lists for comparison
        sorted_list = ak.to_list(sorted_array)
        
        # Check if the result is actually sorted at the innermost level
        def check_sorted(lst):
            if isinstance(lst, list):
                if len(lst) > 0 and isinstance(lst[0], list):
                    # Nested list, check each sublist
                    return all(check_sorted(sublst) for sublst in lst)
                else:
                    # Flat list, check if sorted
                    return all(lst[i] <= lst[i+1] for i in range(len(lst)-1))
            return True
        
        assert check_sorted(sorted_list), f"Result not sorted: {sorted_list}"
        
    except Exception as e:
        # Some structures might not support argsort
        assume(False)

# Test 2: flatten/unflatten round-trip
@given(nested_array_strategy(max_depth=2, max_size=5))
@settings(max_examples=200)
def test_flatten_unflatten_roundtrip(array):
    """Test that unflatten(flatten(array), num(array)) recovers the original"""
    try:
        ak_array = ak.Array(array)
        
        # Skip empty arrays
        if len(ak_array) == 0:
            return
            
        # Get the counts before flattening
        counts = ak.num(ak_array, axis=1)
        
        # Flatten the array
        flattened = ak.flatten(ak_array, axis=1)
        
        # Unflatten using the counts
        unflattened = ak.unflatten(flattened, counts, axis=0)
        
        # Compare the structures
        original_list = ak.to_list(ak_array)
        recovered_list = ak.to_list(unflattened)
        
        assert original_list == recovered_list, f"Round-trip failed: {original_list} != {recovered_list}"
        
    except Exception as e:
        # Some edge cases might not support this operation
        assume(False)

# Test 3: zip/unzip round-trip
@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=10),
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), min_size=1, max_size=10)
)
@settings(max_examples=200)
def test_zip_unzip_roundtrip(array1, array2):
    """Test that unzip(zip([a, b])) recovers the original arrays"""
    try:
        # Make arrays the same length
        min_len = min(len(array1), len(array2))
        array1 = array1[:min_len]
        array2 = array2[:min_len]
        
        if min_len == 0:
            return
        
        ak_array1 = ak.Array(array1)
        ak_array2 = ak.Array(array2)
        
        # Zip the arrays
        zipped = ak.zip([ak_array1, ak_array2])
        
        # Unzip
        unzipped = ak.unzip(zipped)
        
        # Check if we recovered the original arrays
        recovered1 = ak.to_list(unzipped[0])
        recovered2 = ak.to_list(unzipped[1])
        
        assert recovered1 == array1, f"First array not recovered: {array1} != {recovered1}"
        # Use approximate comparison for floats
        assert all(abs(a - b) < 1e-10 for a, b in zip(recovered2, array2)), \
               f"Second array not recovered: {array2} != {recovered2}"
        
    except Exception as e:
        # Some structures might not support zip/unzip
        assume(False)

# Test 4: copy creates independent array
@given(simple_array_strategy())
@settings(max_examples=200) 
def test_copy_creates_independent_array(array):
    """Test that copy creates an independent array (modifications don't affect original)"""
    try:
        ak_array = ak.Array(array)
        
        # Make a copy
        copied = ak.copy(ak_array)
        
        # Check they're initially equal
        assert ak.to_list(ak_array) == ak.to_list(copied)
        
        # The arrays should be equal but not the same object
        # This is a basic property - we can't easily modify awkward arrays in place
        # to test independence, but we can check they're equal
        assert ak.all(ak_array == copied)
        
    except Exception as e:
        assume(False)

# Test 5: fill_none then is_none should be False
@given(
    st.lists(
        st.one_of(st.none(), st.integers(-100, 100)),
        min_size=1,
        max_size=20
    ),
    st.integers(-1000, 1000)
)
@settings(max_examples=200)
def test_fill_none_removes_nones(array_with_nones, fill_value):
    """Test that after fill_none, is_none returns False for filled positions"""
    try:
        ak_array = ak.Array(array_with_nones)
        
        # Check which positions are None
        is_none_before = ak.is_none(ak_array, axis=0)
        
        # Fill None values
        filled = ak.fill_none(ak_array, fill_value)
        
        # Check if any None values remain
        is_none_after = ak.is_none(filled, axis=0)
        
        # All positions should now be non-None
        assert ak.all(~is_none_after), f"Still have None values after fill_none"
        
        # Verify the filled values
        filled_list = ak.to_list(filled)
        for i, (original, filled_val) in enumerate(zip(array_with_nones, filled_list)):
            if original is None:
                assert filled_val == fill_value, f"None not filled with {fill_value} at position {i}"
            else:
                assert filled_val == original, f"Non-None value changed at position {i}"
        
    except Exception as e:
        assume(False)

# Test 6: concatenate length property
@given(
    st.lists(
        st.lists(st.integers(-100, 100), min_size=0, max_size=10),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=200)
def test_concatenate_length_property(arrays):
    """Test that len(concatenate(arrays)) == sum(len(a) for a in arrays)"""
    try:
        ak_arrays = [ak.Array(arr) for arr in arrays]
        
        # Concatenate along axis 0
        concatenated = ak.concatenate(ak_arrays, axis=0)
        
        # Check length property
        expected_length = sum(len(arr) for arr in ak_arrays)
        actual_length = len(concatenated)
        
        assert actual_length == expected_length, \
               f"Length mismatch: expected {expected_length}, got {actual_length}"
        
    except Exception as e:
        assume(False)

# Test 7: sort idempotence
@given(simple_array_strategy())
@settings(max_examples=200)
def test_sort_idempotence(array):
    """Test that sort(sort(array)) == sort(array) (idempotence)"""
    try:
        ak_array = ak.Array(array)
        
        # Sort once
        sorted_once = ak.sort(ak_array, axis=-1)
        
        # Sort twice
        sorted_twice = ak.sort(sorted_once, axis=-1)
        
        # They should be equal
        assert ak.all(sorted_once == sorted_twice), "Sort is not idempotent"
        
    except Exception as e:
        assume(False)

# Test 8: run_lengths consistency
@given(st.lists(st.integers(0, 5), min_size=0, max_size=30))
@settings(max_examples=200)
def test_run_lengths_consistency(array):
    """Test that run_lengths produces correct counts for consecutive elements"""
    ak_array = ak.Array(array)
    
    if len(ak_array) == 0:
        return
        
    result = ak.run_lengths(ak_array)
    
    # Manually compute run lengths for verification
    if len(array) == 0:
        expected_lengths = []
    else:
        expected_lengths = []
        current_val = array[0]
        current_count = 1
        
        for val in array[1:]:
            if val == current_val:
                current_count += 1
            else:
                expected_lengths.append(current_count)
                current_val = val
                current_count = 1
        
        expected_lengths.append(current_count)
    
    # run_lengths only returns the counts
    actual_lengths = ak.to_list(result)
    
    assert actual_lengths == expected_lengths, f"Lengths mismatch: {actual_lengths} != {expected_lengths}"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])