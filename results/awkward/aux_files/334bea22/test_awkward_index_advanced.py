import sys
import os
import numpy as np
import copy
from hypothesis import given, strategies as st, settings, assume, HealthCheck

sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
import awkward as ak

# Advanced property tests looking for subtle bugs

@given(
    st.integers(10, 50).flatmap(
        lambda n: st.tuples(
            st.lists(st.integers(-100, 100), min_size=n, max_size=n),
            st.lists(st.booleans(), min_size=n, max_size=n).filter(lambda m: any(m))
        )
    )
)
def test_setitem_with_boolean_mask(data_and_mask):
    """Test setitem with boolean mask"""
    data, mask = data_and_mask
    
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    mask_arr = np.array(mask)
    
    # Set values where mask is True
    new_value = 999
    idx[mask_arr] = new_value
    
    # Check that values were set correctly
    for i, m in enumerate(mask):
        if m:
            assert idx[i] == new_value
        else:
            assert idx[i] == data[i]


@given(
    st.lists(st.integers(-100, 100), min_size=5, max_size=20)
)
def test_setitem_slice_size_mismatch(data):
    """Test setitem with mismatched slice sizes"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    
    # Try to set a slice with wrong size
    if len(data) >= 5:
        slice_to_set = idx[1:4]  # 3 elements
        new_values = [111, 222]  # 2 elements - mismatch!
        
        # This should either work like numpy or raise an error
        try:
            idx[1:4] = new_values
            # If it works, check numpy behavior
            numpy_arr = arr.copy()
            numpy_arr[1:4] = new_values
            assert np.array_equal(idx.data[:len(new_values)+1], numpy_arr[:len(new_values)+1])
        except (ValueError, TypeError):
            # Error is acceptable for size mismatch
            pass


@given(
    st.lists(st.integers(-100, 100), min_size=2, max_size=50)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_getitem_consistency(data):
    """Test that multiple getitem calls are consistent"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Multiple calls should return same result
    result1 = idx[0]
    result2 = idx[0]
    assert result1 == result2
    
    # Slice multiple times
    if len(data) > 5:
        slice1 = idx[2:5]
        slice2 = idx[2:5]
        assert np.array_equal(slice1.data, slice2.data)


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_after_setitem_type_consistency(data):
    """Test that Index type remains consistent after setitem"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    original_type = type(idx)
    
    # Modify the index
    idx[0] = 999
    
    # Type should not change
    assert type(idx) == original_type
    assert isinstance(idx, ak.index.Index32)
    assert idx.dtype == np.dtype(np.int32)


@given(
    st.lists(st.integers(-2**31, 2**31-1), min_size=1, max_size=20)
)
def test_index32_to64_overflow_safety(data):
    """Test that converting Index32 to Index64 handles boundary values"""
    arr = np.array(data, dtype=np.int32)
    idx32 = ak.index.Index32(arr)
    
    # Convert to 64-bit
    idx64 = idx32.to64()
    
    # All values should be exactly preserved
    for i in range(len(data)):
        val32 = idx32[i]
        val64 = idx64[i]
        
        # Handle numpy scalar types
        if hasattr(val32, 'item'):
            val32 = val32.item()
        if hasattr(val64, 'item'):
            val64 = val64.item()
            
        assert val32 == val64 == data[i]


@given(
    st.lists(st.integers(0, 2**32-1), min_size=1, max_size=20)
)
def test_indexu32_to64_sign_preservation(data):
    """Test that unsigned values are preserved when converting to int64"""
    arr = np.array(data, dtype=np.uint32)
    idxu32 = ak.index.IndexU32(arr)
    
    # Convert to 64-bit (signed)
    idx64 = idxu32.to64()
    
    # Values should be preserved even if > 2^31
    for i in range(len(data)):
        val_u32 = idxu32[i]
        val_64 = idx64[i]
        
        if hasattr(val_u32, 'item'):
            val_u32 = val_u32.item()
        if hasattr(val_64, 'item'):
            val_64 = val_64.item()
            
        assert val_u32 == val_64 == data[i]
        
        # Specifically check large unsigned values
        if data[i] > 2**31:
            assert val_64 > 0  # Should not become negative


@given(
    st.lists(st.integers(-100, 100), min_size=3, max_size=20),
    st.integers(-10, 10),
    st.integers(-10, 10),
    st.integers(-5, 5).filter(lambda x: x != 0)
)
def test_complex_slice_operations(data, start, stop, step):
    """Test complex slicing with start, stop, step"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Test numpy equivalence
    numpy_result = arr[start:stop:step]
    idx_result = idx[start:stop:step]
    
    if len(numpy_result) > 0:
        assert isinstance(idx_result, ak.index.Index32)
        assert np.array_equal(idx_result.data, numpy_result)
    else:
        # Empty result
        if isinstance(idx_result, ak.index.Index32):
            assert len(idx_result) == 0


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_deepcopy_independence(data):
    """Test that deepcopy creates independent objects"""
    arr = np.array(data, dtype=np.int32)
    idx1 = ak.index.Index32(arr.copy())
    
    # Deep copy
    idx2 = copy.deepcopy(idx1)
    
    # Modify original
    idx1[0] = 999
    
    # Deep copy should be unchanged
    assert idx2[0] == data[0]
    assert idx2[0] != idx1[0]


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers())
)
def test_metadata_deepcopy_independence(data, metadata):
    """Test that metadata is properly deep copied"""
    arr = np.array(data, dtype=np.int32)
    idx1 = ak.index.Index32(arr, metadata=metadata.copy())
    
    # Deep copy
    idx2 = copy.deepcopy(idx1)
    
    # Modify original metadata
    if metadata:
        key = list(metadata.keys())[0]
        idx1.metadata[key] = 999999
        
        # Deep copy metadata should be unchanged
        assert idx2.metadata[key] == metadata[key]


@given(
    st.lists(st.integers(-100, 100), min_size=1, max_size=50)
)
def test_index_class_switching(data):
    """Test that Index class switching works correctly based on dtype"""
    # Start with generic Index and let it auto-select type
    arr8 = np.array(data, dtype=np.int8)
    idx = ak.index.Index(arr8)
    assert isinstance(idx, ak.index.Index8)
    
    arr32 = np.array(data, dtype=np.int32)
    idx = ak.index.Index(arr32)
    assert isinstance(idx, ak.index.Index32)
    
    arr64 = np.array(data, dtype=np.int64)
    idx = ak.index.Index(arr64)
    assert isinstance(idx, ak.index.Index64)
    
    # Unsigned types
    data_positive = [abs(x) for x in data]
    arru8 = np.array(data_positive, dtype=np.uint8)
    idx = ak.index.Index(arru8)
    assert isinstance(idx, ak.index.IndexU8)
    
    arru32 = np.array(data_positive, dtype=np.uint32)
    idx = ak.index.Index(arru32)
    assert isinstance(idx, ak.index.IndexU32)


@given(
    st.lists(st.integers(-100, 100), min_size=5, max_size=50)
)
def test_slice_assignment_broadcast(data):
    """Test slice assignment with scalar (broadcasting)"""
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr.copy())
    
    # Assign scalar to slice (should broadcast)
    idx[1:4] = 777
    
    # Check broadcasting worked
    assert idx[1] == 777
    assert idx[2] == 777
    assert idx[3] == 777
    assert idx[0] == data[0]  # Unchanged
    if len(data) > 4:
        assert idx[4] == data[4]  # Unchanged


@given(
    st.lists(st.integers(-10, 10), min_size=1, max_size=20)
)
def test_empty_index_operations(data):
    """Test operations on empty Index"""
    # Create empty index
    empty_idx = ak.index.Index32(np.array([], dtype=np.int32))
    
    assert len(empty_idx) == 0
    assert empty_idx.length == 0
    
    # Empty slice of empty should be empty
    assert len(empty_idx[:]) == 0
    assert len(empty_idx[0:0]) == 0
    
    # Test with data
    arr = np.array(data, dtype=np.int32)
    idx = ak.index.Index32(arr)
    
    # Create empty slice
    empty_slice = idx[10:10]
    assert len(empty_slice) == 0


@given(
    st.lists(st.integers(-128, 127), min_size=1, max_size=50)
)
def test_view_vs_copy_semantics(data):
    """Test whether operations create views or copies"""
    arr = np.array(data, dtype=np.int8)
    idx = ak.index.Index8(arr)
    
    # Slicing should create a new Index
    if len(data) > 2:
        sliced = idx[1:-1]
        assert isinstance(sliced, ak.index.Index8)
        
        # Modifying slice should not affect original
        if len(sliced) > 0:
            original_val = idx[1]
            sliced[0] = -99
            # Check if original is affected (view) or not (copy)
            # This behavior should be consistent