import sys
import os
import numpy as np
import copy
from hypothesis import given, strategies as st, settings, assume, example

sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
import awkward as ak

# More sophisticated property tests

@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=100)
)
def test_index_form_property_correct(data):
    """Test that Index types have correct form strings"""
    # Test int8
    idx8 = ak.index.Index8(np.array(data, dtype=np.int8))
    assert idx8.form == "i8"
    
    # Test uint8 with appropriate data
    data_uint8 = [abs(x) for x in data]
    idxu8 = ak.index.IndexU8(np.array(data_uint8, dtype=np.uint8))
    assert idxu8.form == "u8"
    
    # Test int32
    idx32 = ak.index.Index32(np.array(data, dtype=np.int32))
    assert idx32.form == "i32"
    
    # Test uint32 with appropriate data
    idxu32 = ak.index.IndexU32(np.array(data_uint8, dtype=np.uint32))
    assert idxu32.form == "u32"
    
    # Test int64
    idx64 = ak.index.Index64(np.array(data, dtype=np.int64))
    assert idx64.form == "i64"


@given(
    st.lists(st.integers(-100, 100), min_size=2, max_size=50),
    st.integers(),
    st.integers()
)
def test_index_slice_bounds(data, start, stop):
    """Test that slicing with various bounds works correctly"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test numpy slicing equivalence
    try:
        numpy_result = arr[start:stop]
        idx_result = idx[start:stop]
        
        if len(numpy_result) > 0:
            assert isinstance(idx_result, ak.index.Index32)
            assert np.array_equal(idx_result.data, numpy_result)
        else:
            # Empty slice
            assert isinstance(idx_result, ak.index.Index32)
            assert len(idx_result) == 0
    except Exception as e:
        # If numpy raises an exception, Index should too
        try:
            idx[start:stop]
            assert False, f"Index should have raised exception like numpy: {e}"
        except:
            pass


@given(
    st.lists(st.integers(-1000, 1000), min_size=1, max_size=100)
)
def test_index_setitem_preserves_dtype(data):
    """Test that setitem preserves the dtype of the Index"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    
    # Set a value
    if len(data) > 0:
        idx[0] = 999
        assert idx.dtype == np.dtype(np.int32)
        assert idx[0] == 999
        
        # Set with a slice
        if len(data) > 2:
            idx[1:3] = [111, 222]
            assert idx.dtype == np.dtype(np.int32)
            assert idx[1] == 111
            assert idx[2] == 222


@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=50)
)
def test_index8_overflow_behavior(data):
    """Test what happens when Index8 values might overflow"""
    arr = np.array(data, dtype=np.int8)
    idx = ak.index.Index8(arr)
    
    # Convert to 64-bit and back
    idx64 = idx.to64()
    
    # All values should be preserved in conversion
    assert np.array_equal(idx64.data, arr.astype(np.int64))
    
    # Test that Index8 properly handles its range
    assert idx.dtype == np.dtype(np.int8)
    for i, val in enumerate(data):
        assert idx[i] == val


@given(
    st.lists(st.integers(0, 255), min_size=1, max_size=50)
)
def test_indexu8_unsigned_behavior(data):
    """Test that unsigned index properly handles unsigned values"""
    arr = np.array(data, dtype=np.uint8)
    idx = ak.index.IndexU8(arr)
    
    # All values should be non-negative
    assert np.all(idx.data >= 0)
    
    # Test conversion to 64-bit preserves unsigned values
    idx64 = idx.to64()
    assert np.array_equal(idx64.data, arr.astype(np.int64))


@given(
    st.one_of(
        st.just(np.int8),
        st.just(np.uint8),
        st.just(np.int32),
        st.just(np.uint32),
        st.just(np.int64)
    ),
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_auto_type_detection(dtype, data):
    """Test that Index() automatically selects the right subclass"""
    arr = np.array(data, dtype=dtype)
    idx = ak.index.Index(arr)
    
    # Check that the right subclass was selected
    if dtype == np.int8:
        assert isinstance(idx, ak.index.Index8)
        assert idx.form == "i8"
    elif dtype == np.uint8:
        assert isinstance(idx, ak.index.IndexU8)
        assert idx.form == "u8"
    elif dtype == np.int32:
        assert isinstance(idx, ak.index.Index32)
        assert idx.form == "i32"
    elif dtype == np.uint32:
        assert isinstance(idx, ak.index.IndexU32)
        assert idx.form == "u32"
    elif dtype == np.int64:
        assert isinstance(idx, ak.index.Index64)
        assert idx.form == "i64"


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    st.lists(st.integers(), min_size=1, max_size=10)
)
def test_index_fancy_indexing(data, indices):
    """Test fancy indexing with integer arrays"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Create valid indices within bounds
    valid_indices = [i % len(data) for i in indices]
    indices_arr = np.array(valid_indices, dtype=np.int32)
    
    # Test fancy indexing
    numpy_result = arr[indices_arr]
    idx_result = idx[indices_arr]
    
    assert isinstance(idx_result, ak.index.Index32)
    assert np.array_equal(idx_result.data, numpy_result)


@given(
    st.lists(st.integers(-100, 100), min_size=3, max_size=50)
)
def test_index_boolean_masking(data):
    """Test boolean mask indexing"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Create a boolean mask
    mask = arr > 0
    
    # Test boolean indexing
    numpy_result = arr[mask]
    idx_result = idx[mask]
    
    if len(numpy_result) > 0:
        assert isinstance(idx_result, ak.index.Index32)
        assert np.array_equal(idx_result.data, numpy_result)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_metadata_preservation(data):
    """Test that metadata is preserved through operations"""
    arr = np.array(data, dtype=np.int32)
    metadata = {"key": "value", "number": 42}
    
    idx = ak.index.Index32(arr, metadata=metadata)
    
    # Check metadata is accessible
    assert idx.metadata == metadata
    
    # Test metadata survives slicing
    if len(data) > 2:
        sliced = idx[1:-1]
        assert sliced.metadata == metadata
    
    # Test metadata survives copy
    copied = copy.copy(idx)
    assert copied.metadata == metadata


@given(
    st.lists(st.integers(-2**31, 2**31-1), min_size=1, max_size=20)
)
def test_index32_boundary_values(data):
    """Test Index32 with values at int32 boundaries"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Check all values are preserved correctly
    for i, val in enumerate(data):
        retrieved = idx[i]
        # Need to handle numpy scalar conversion
        if isinstance(retrieved, np.integer):
            retrieved = int(retrieved)
        assert retrieved == val, f"Value at index {i}: expected {val}, got {retrieved}"
    
    # Test conversion to int64 preserves values
    idx64 = idx.to64()
    assert np.array_equal(idx64.data, arr.astype(np.int64))


@given(
    st.lists(st.integers(0, 2**32-1), min_size=1, max_size=20)
)
def test_indexu32_boundary_values(data):
    """Test IndexU32 with values at uint32 boundaries"""
    arr = np.array(data, dtype=np.uint32)
    idx = ak.index.IndexU32(arr)
    
    # Check all values are preserved correctly
    for i, val in enumerate(data):
        retrieved = idx[i]
        if isinstance(retrieved, np.integer):
            retrieved = int(retrieved)
        assert retrieved == val, f"Value at index {i}: expected {val}, got {retrieved}"


@given(
    st.lists(st.integers(-100, 100), min_size=2, max_size=50)
)
def test_index_empty_slice_behavior(data):
    """Test behavior with empty slices"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Empty slice in middle
    empty = idx[5:5]
    assert isinstance(empty, ak.index.Index32)
    assert len(empty) == 0
    
    # Reversed slice (should be empty)
    empty = idx[10:5]
    assert isinstance(empty, ak.index.Index32)
    assert len(empty) == 0


@given(
    st.integers(-1000, 1000)
)
def test_index_scalar_construction(value):
    """Test Index construction with scalar values"""
    # Single scalar should be converted to 1D array
    idx = ak.index.Index(np.array([value], dtype=np.int32))
    assert len(idx) == 1
    assert idx[0] == value


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_step_slicing(data):
    """Test slicing with various step values"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test various step values
    for step in [-3, -2, -1, 1, 2, 3]:
        numpy_result = arr[::step]
        idx_result = idx[::step]
        
        assert isinstance(idx_result, ak.index.Index32)
        assert np.array_equal(idx_result.data, numpy_result)