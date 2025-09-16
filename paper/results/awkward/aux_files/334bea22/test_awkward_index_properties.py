import sys
import os
import numpy as np
import copy
from hypothesis import given, strategies as st, settings, assume

sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
import awkward as ak

@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=100)
)
def test_index_roundtrip_int8(data):
    """Test that Index preserves data through round-trip indexing"""
    arr = np.array(data, dtype=np.int8)
    idx = ak.index.Index8(arr)
    
    # Full slice should return all data
    result = idx[:]
    assert isinstance(result, ak.index.Index8)
    assert np.array_equal(result.data, arr)
    
    # Individual elements should match
    for i in range(len(data)):
        assert idx[i] == arr[i]


@given(
    st.lists(st.integers(0, 255), min_size=1, max_size=100)
)
def test_index_roundtrip_uint8(data):
    """Test that IndexU8 preserves unsigned data"""
    arr = np.array(data, dtype=np.uint8)
    idx = ak.index.IndexU8(arr)
    
    result = idx[:]
    assert isinstance(result, ak.index.IndexU8)
    assert np.array_equal(result.data, arr)


@given(
    st.lists(st.integers(-2147483648, 2147483647), min_size=1, max_size=100)
)
def test_index_roundtrip_int32(data):
    """Test that Index32 preserves 32-bit signed data"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    result = idx[:]
    assert isinstance(result, ak.index.Index32)
    assert np.array_equal(result.data, arr)


@given(
    st.lists(st.integers(0, 4294967295), min_size=1, max_size=100)
)
def test_index_roundtrip_uint32(data):
    """Test that IndexU32 preserves 32-bit unsigned data"""
    arr = np.array(data, dtype=np.uint32)
    idx = ak.index.IndexU32(arr)
    
    result = idx[:]
    assert isinstance(result, ak.index.IndexU32)
    assert np.array_equal(result.data, arr)


@given(
    st.lists(st.integers(-1000000, 1000000), min_size=1, max_size=100)
)
def test_index_length_invariant(data):
    """Test that Index preserves length"""
    arr = np.array(data, dtype=np.int64)
    idx = ak.index.Index64(arr)
    
    assert len(idx) == len(data)
    assert idx.length == len(data)


@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=100)
)
def test_index_to64_conversion(data):
    """Test that to64() correctly converts to int64"""
    arr = np.array(data, dtype=np.int8)
    idx = ak.index.Index8(arr)
    
    idx64 = idx.to64()
    assert isinstance(idx64, ak.index.Index64)
    assert idx64.dtype == np.dtype(np.int64)
    
    # Values should be preserved
    assert np.array_equal(idx64.data, arr.astype(np.int64))


@given(
    st.lists(st.integers(-1000, 1000), min_size=1, max_size=100)
)
def test_index_copy_semantics(data):
    """Test that copy operations work correctly"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Shallow copy
    idx_copy = copy.copy(idx)
    assert isinstance(idx_copy, ak.index.Index32)
    assert np.array_equal(idx_copy.data, idx.data)
    
    # Deep copy
    idx_deep = copy.deepcopy(idx)
    assert isinstance(idx_deep, ak.index.Index32)
    assert np.array_equal(idx_deep.data, idx.data)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_equality(data1, data2):
    """Test is_equal_to method"""
    arr1 = np.array(data1, dtype=np.int32)
    arr2 = np.array(data2, dtype=np.int32)
    
    idx1 = ak.index.Index32(arr1)
    idx2 = ak.index.Index32(arr2)
    
    should_be_equal = np.array_equal(arr1, arr2)
    assert idx1.is_equal_to(idx2) == should_be_equal
    
    # Same index should be equal to itself
    assert idx1.is_equal_to(idx1)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    st.integers(0, 49)
)
def test_index_getitem_setitem(data, idx_pos):
    """Test getitem and setitem operations"""
    assume(idx_pos < len(data))
    
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Get item
    assert idx[idx_pos] == arr[idx_pos]
    
    # Set item
    new_value = 999
    idx[idx_pos] = new_value
    assert idx[idx_pos] == new_value


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_slicing(data):
    """Test various slicing operations"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test different slice patterns
    if len(data) > 1:
        # First half
        half = len(data) // 2
        result = idx[:half]
        assert isinstance(result, ak.index.Index32)
        assert np.array_equal(result.data, arr[:half])
        
        # Last half
        result = idx[half:]
        assert isinstance(result, ak.index.Index32)
        assert np.array_equal(result.data, arr[half:])
        
        # Step slicing
        result = idx[::2]
        assert isinstance(result, ak.index.Index32)
        assert np.array_equal(result.data, arr[::2])


@given(
    st.integers(1, 5),
    st.integers(1, 10)
)
def test_index_rejects_multidimensional(rows, cols):
    """Test that Index rejects multi-dimensional arrays"""
    data = np.ones((rows, cols), dtype=np.int32)
    
    try:
        idx = ak.index.Index(data)
        # Should have raised TypeError
        assert False, "Expected TypeError for multi-dimensional data"
    except TypeError as e:
        assert "one-dimensional" in str(e)


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000), 
             min_size=1, max_size=50)
)
def test_index_dtype_conversion(float_data):
    """Test that Index converts float data to integer types"""
    arr_float = np.array(float_data, dtype=np.float64)
    
    # Create Index32 with float data - should convert to int32
    idx = ak.index.Index32(arr_float)
    assert idx.dtype == np.dtype(np.int32)
    
    # Values should be truncated/converted to integers
    expected = arr_float.astype(np.int32)
    assert np.array_equal(idx.data, expected)


@given(
    st.lists(st.integers(0, 255), min_size=1, max_size=100)
)
def test_index_form_property(data):
    """Test that Index types have correct form strings"""
    # Test each Index type's form property
    idx8 = ak.index.Index8(np.array(data, dtype=np.int8))
    assert idx8.form == "i8"
    
    idxu8 = ak.index.IndexU8(np.array(data, dtype=np.uint8))
    assert idxu8.form == "u8"
    
    idx32 = ak.index.Index32(np.array(data, dtype=np.int32))
    assert idx32.form == "i32"
    
    idxu32 = ak.index.IndexU32(np.array(data, dtype=np.uint32))
    assert idxu32.form == "u32"
    
    idx64 = ak.index.Index64(np.array(data, dtype=np.int64))
    assert idx64.form == "i64"


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_negative_indexing(data):
    """Test negative indexing works like numpy arrays"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test negative indices
    assert idx[-1] == arr[-1]
    if len(data) > 1:
        assert idx[-2] == arr[-2]
    
    # Negative slicing
    result = idx[-3:]
    expected = arr[-3:]
    if len(expected) > 0:
        assert isinstance(result, ak.index.Index32)
        assert np.array_equal(result.data, expected)