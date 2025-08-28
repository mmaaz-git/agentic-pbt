import sys
import os
import numpy as np
import copy
from hypothesis import given, strategies as st, settings, assume, example

sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
import awkward as ak

# Tests targeting specific potential bugs based on code analysis

@given(
    st.lists(st.integers(-2**63, 2**63-1), min_size=1, max_size=10)
)
def test_longlong_edge_cases(data):
    """Test edge cases with longlong conversion to int64"""
    # Create array with explicit longlong dtype
    arr = np.array(data, dtype=np.longlong)
    
    # Index should convert to int64
    idx = ak.index.Index(arr)
    
    # Check conversion happened
    assert idx.dtype == np.dtype(np.int64)
    
    # Check extreme values are preserved
    for i, val in enumerate(data):
        result = idx[i]
        if hasattr(result, 'item'):
            result = result.item()
        assert result == val


@given(
    st.lists(st.integers(-100, 100), min_size=2, max_size=50)
)
def test_non_contiguous_input(data):
    """Test that non-contiguous arrays are made contiguous"""
    arr = np.array(data + data, dtype=np.int32)  # Double the data
    
    # Create non-contiguous view by striding
    non_contiguous = arr[::2]  # Every other element
    if len(non_contiguous) > 1:
        assert not non_contiguous.flags['C_CONTIGUOUS']
    
    # Index should make it contiguous
    idx = ak.index.Index32(non_contiguous)
    
    # Result should be contiguous
    assert idx.data.flags['C_CONTIGUOUS'] or idx.data.flags['F_CONTIGUOUS']
    
    # Data should match
    assert np.array_equal(idx.data, non_contiguous)


@given(
    st.lists(st.integers(-100, 100), min_size=5, max_size=50),
    st.integers()
)
def test_out_of_bounds_indexing(data, index):
    """Test behavior with out-of-bounds indices"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test numpy equivalence for out-of-bounds
    if abs(index) > len(data) * 10:  # Very out of bounds
        try:
            numpy_result = arr[index]
            idx_result = idx[index]
            assert False, "Both should raise for out of bounds"
        except IndexError:
            # Numpy raised, Index should too
            try:
                idx[index]
                assert False, "Index should raise IndexError like numpy"
            except IndexError:
                pass  # Expected


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_fortran_order_arrays(data):
    """Test handling of Fortran-ordered arrays"""
    # Create Fortran-ordered array
    arr = np.array(data, dtype=np.int32, order='F')
    
    # Index should handle it
    idx = ak.index.Index32(arr)
    
    # Should be contiguous (either C or F)
    assert idx.data.flags['C_CONTIGUOUS'] or idx.data.flags['F_CONTIGUOUS']
    
    # Data preserved
    assert np.array_equal(idx.data, arr)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_slice_normalization_edge_cases(data):
    """Test edge cases in slice normalization"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test various slice edge cases that might trigger normalize_slice
    
    # Slice with None values
    result = idx[None:None:None]
    assert np.array_equal(result.data, arr)
    
    # Negative step with no start/stop
    result = idx[::-1]
    assert np.array_equal(result.data, arr[::-1])
    
    # Large negative indices
    if len(data) > 0:
        result = idx[-len(data):]
        assert np.array_equal(result.data, arr)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_zero_length_operations(data):
    """Test operations that result in zero-length indices"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Create zero-length slice
    zero_slice = idx[0:0]
    assert len(zero_slice) == 0
    assert zero_slice.length == 0
    assert isinstance(zero_slice, ak.index.Index32)
    
    # Operations on zero-length
    assert zero_slice._nbytes_part() == 0  # Use the actual method
    repr_str = repr(zero_slice)
    assert "len=" in repr_str


@given(
    st.integers(-2**7, 2**7-1)
)
def test_single_element_index_operations(value):
    """Test operations on single-element indices"""
    arr = np.array([value], dtype=np.int8)
    idx = ak.index.Index8(arr)
    
    # Length
    assert len(idx) == 1
    assert idx.length == 1
    
    # Indexing
    assert idx[0] == value
    assert idx[-1] == value
    
    # Slicing
    full = idx[:]
    assert len(full) == 1
    assert full[0] == value
    
    # Empty slices
    empty = idx[1:]
    assert len(empty) == 0
    
    # to64 conversion
    idx64 = idx.to64()
    assert idx64[0] == value
    assert idx64.dtype == np.dtype(np.int64)


@given(
    st.lists(st.integers(0, 255), min_size=1, max_size=50)
)
def test_unsigned_negative_indexing(data):
    """Test negative indexing with unsigned indices"""
    arr = np.array(data, dtype=np.uint8)
    idx = ak.index.IndexU8(arr)
    
    # Negative indexing should work
    assert idx[-1] == data[-1]
    
    if len(data) > 1:
        assert idx[-2] == data[-2]
        
    # Negative slicing
    last_three = idx[-3:]
    expected = arr[-3:]
    assert np.array_equal(last_three.data, expected)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    st.lists(st.integers(-200, 200), min_size=1, max_size=50)
)
def test_is_equal_to_different_lengths(data1, data2):
    """Test is_equal_to with different length indices"""
    assume(len(data1) != len(data2))
    
    arr1 = np.array(data1, dtype=np.int32)
    arr2 = np.array(data2, dtype=np.int32)
    
    idx1 = ak.index.Index32(arr1)
    idx2 = ak.index.Index32(arr2)
    
    # Different lengths should not be equal
    assert not idx1.is_equal_to(idx2)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=20)
)
def test_chained_slicing(data):
    """Test chaining multiple slice operations"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    if len(data) >= 10:
        # Chain slices
        result = idx[2:][1:][:-1]
        expected = arr[2:][1:][:-1]
        
        assert isinstance(result, ak.index.Index32)
        assert np.array_equal(result.data, expected)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_slice_with_step_zero(data):
    """Test that step=0 in slice is handled properly"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Step of 0 should raise ValueError like numpy
    try:
        numpy_result = arr[::0]
        assert False, "Numpy should raise for step=0"
    except ValueError:
        pass
    
    try:
        idx_result = idx[::0]
        assert False, "Index should raise for step=0 like numpy"
    except (ValueError, ZeroDivisionError):
        pass  # Expected


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_mixed_type_setitem(data):
    """Test setitem with different numeric types"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    
    # Set with float (should convert to int)
    idx[0] = 99.7
    assert idx[0] == 99  # Should truncate
    
    # Set with numpy scalar
    idx[0] = np.int64(88)
    assert idx[0] == 88
    
    # Set slice with mixed types
    if len(data) >= 3:
        idx[0:3] = [1.1, 2.9, 3.5]
        assert idx[0] == 1
        assert idx[1] == 2
        assert idx[2] == 3