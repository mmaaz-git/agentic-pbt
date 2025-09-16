import sys
import os
import numpy as np
import copy
from hypothesis import given, strategies as st, settings, assume, example

sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
import awkward as ak

# Edge case and boundary tests

@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=100)
)
def test_index_contiguous_memory(data):
    """Test that Index ensures contiguous memory layout"""
    # Create non-contiguous array
    arr = np.array(data, dtype=np.int8)
    non_contiguous = arr[::2] if len(arr) > 1 else arr
    
    # Index should make it contiguous
    idx = ak.index.Index8(non_contiguous)
    assert idx.data.flags['C_CONTIGUOUS'] or idx.data.flags['F_CONTIGUOUS']


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_zeros_empty_construction(data):
    """Test zeros and empty class methods"""
    length = len(data)
    
    # Test zeros
    idx_zeros = ak.index.Index32.zeros(length, nplike=ak.index.numpy)
    assert len(idx_zeros) == length
    assert np.all(idx_zeros.data == 0)
    assert idx_zeros.dtype == np.dtype(np.int32)
    
    # Test empty
    idx_empty = ak.index.Index32.empty(length, nplike=ak.index.numpy)
    assert len(idx_empty) == length
    assert idx_empty.dtype == np.dtype(np.int32)


@given(
    st.lists(st.integers(-2**63, 2**63-1), min_size=1, max_size=10)
)
def test_index_int64_longlong_conversion(data):
    """Test that longlong is properly converted to int64"""
    # Create array with longlong dtype
    arr = np.array(data, dtype=np.longlong)
    idx = ak.index.Index(arr)
    
    # Should be converted to int64
    assert idx.dtype == np.dtype(np.int64)
    assert isinstance(idx, ak.index.Index64)
    
    # Values should be preserved
    for i, val in enumerate(data):
        assert idx[i] == val


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_is_equal_to_index_dtype_flag(data):
    """Test is_equal_to with index_dtype parameter"""
    arr1 = np.array(data, dtype=np.int32)
    arr2 = np.array(data, dtype=np.int64)
    
    idx32 = ak.index.Index32(arr1)
    idx64 = ak.index.Index64(arr2)
    
    # With index_dtype=True (default), different dtypes should not be equal
    assert not idx32.is_equal_to(idx64, index_dtype=True)
    
    # With index_dtype=False, should compare values only
    assert idx32.is_equal_to(idx64, index_dtype=False)
    
    # Same dtype should be equal
    idx32_2 = ak.index.Index32(arr1.copy())
    assert idx32.is_equal_to(idx32_2, index_dtype=True)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_double_wrapping(data):
    """Test that Index cannot wrap another Index"""
    arr = np.array(data, dtype=np.int32)
    idx1 = ak.index.Index32(arr)
    
    # Should raise assertion error when trying to wrap an Index
    try:
        idx2 = ak.index.Index(idx1)
        assert False, "Should not allow wrapping an Index with another Index"
    except AssertionError:
        pass  # Expected


@given(
    st.text(min_size=1, max_size=10),
    st.integers()
)
def test_index_metadata_type_validation(text_key, int_value):
    """Test that metadata must be a dict"""
    arr = np.array([1, 2, 3], dtype=np.int32)
    
    # Valid metadata (dict)
    idx = ak.index.Index32(arr, metadata={text_key: int_value})
    assert idx.metadata[text_key] == int_value
    
    # Invalid metadata (not a dict)
    try:
        idx = ak.index.Index32(arr, metadata="not a dict")
        assert False, "Should reject non-dict metadata"
    except TypeError as e:
        assert "dict" in str(e)


@given(
    st.lists(st.floats(allow_nan=True, allow_infinity=True), min_size=1, max_size=50)
)
def test_index_nan_inf_handling(float_data):
    """Test how Index handles NaN and infinity values when converting from float"""
    arr_float = np.array(float_data, dtype=np.float64)
    
    # Converting float with NaN/inf to int should follow numpy behavior
    try:
        expected = arr_float.astype(np.int32)
        idx = ak.index.Index32(arr_float)
        assert np.array_equal(idx.data, expected, equal_nan=True)
    except (ValueError, RuntimeError) as e:
        # If numpy raises an error, Index should too
        try:
            idx = ak.index.Index32(arr_float)
            assert False, f"Index should have raised error like numpy: {e}"
        except:
            pass


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_property_accessors(data):
    """Test various property accessors"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test properties
    assert idx.nplike == ak.index.numpy
    assert idx.length == len(data)
    assert hasattr(idx, 'ptr')  # Should have ptr property
    
    # Test form property
    assert idx.form in ["i8", "u8", "i32", "u32", "i64"]


@given(
    st.lists(st.integers(0, 65535), min_size=1, max_size=50)
)
def test_unsupported_dtype_rejection(data):
    """Test that unsupported dtypes are rejected"""
    # Try to create Index with int16 (not supported)
    arr = np.array(data, dtype=np.int16)
    
    try:
        idx = ak.index.Index(arr)
        # If it doesn't raise, check what dtype it converted to
        assert idx.dtype in [np.dtype(np.int8), np.dtype(np.uint8), 
                             np.dtype(np.int32), np.dtype(np.uint32), 
                             np.dtype(np.int64)]
    except TypeError as e:
        assert "int8, uint8, int32, uint32, int64" in str(e)


@given(
    st.lists(st.integers(-100, 100), min_size=2, max_size=50)
)
def test_index_slice_with_none(data):
    """Test slicing with None values"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test slice with None start
    result = idx[None:5]
    expected = arr[None:5]
    assert np.array_equal(result.data, expected)
    
    # Test slice with None stop
    result = idx[5:None]
    expected = arr[5:None]
    assert np.array_equal(result.data, expected)
    
    # Test slice with None step
    result = idx[::None]
    expected = arr[::None]
    assert np.array_equal(result.data, expected)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_nbytes(data):
    """Test _nbytes_part method"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # nbytes should match the underlying array
    assert idx._nbytes_part() == arr.nbytes
    assert idx._nbytes_part() == len(data) * 4  # int32 is 4 bytes


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_repr_doesnt_crash(data):
    """Test that __repr__ doesn't crash on various inputs"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Should be able to get repr without crashing
    repr_str = repr(idx)
    assert "Index" in repr_str
    assert "dtype=" in repr_str
    assert "len=" in repr_str
    
    # Test _repr with different parameters
    repr_str = idx._repr("  ", "PREFIX", "SUFFIX")
    assert "PREFIX" in repr_str
    assert "SUFFIX" in repr_str


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=200)
)
def test_index_repr_truncation(data):
    """Test that repr truncates long arrays properly"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    repr_str = repr(idx)
    lines = repr_str.split('\n')
    
    # Check truncation happens for long arrays
    if len(data) > 100:
        # Should see ellipsis for truncation
        full_repr = idx._repr("", "", "")
        if '\n' in full_repr and len(lines) > 5:
            assert any('...' in line for line in lines)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_to_nplike(data):
    """Test to_nplike method"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Convert to same nplike (should work)
    idx2 = idx.to_nplike(ak.index.numpy)
    assert isinstance(idx2, ak.index.Index32)
    assert np.array_equal(idx2.data, idx.data)