import numpy as np
import ctypes
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# Focus on finding bugs in specific edge cases

# Test 1: Check behavior with F-contiguous arrays
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=4, max_size=20))
@settings(max_examples=500)
def test_f_contiguous_round_trip(values):
    """Test F-contiguous array handling"""
    # Create a 2D array and make it F-contiguous
    size = len(values)
    if size < 4:
        return
    
    rows = 2
    cols = size // rows
    values = values[:rows*cols]
    
    # Create F-contiguous array
    arr = np.array(values, dtype=np.int32).reshape((rows, cols), order='F')
    assert arr.flags['F_CONTIGUOUS']
    
    # Convert to ctypes
    ct = np.ctypeslib.as_ctypes(arr)
    
    # Convert back
    arr2 = np.ctypeslib.as_array(ct)
    
    # Check data is preserved
    assert np.array_equal(arr, arr2), f"Data not preserved for F-contiguous array"
    

# Test 2: Check with various byte orders (endianness)
@given(st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=10))
@settings(max_examples=200)
def test_endianness_handling(values):
    """Test arrays with different byte orders"""
    arr_native = np.array(values, dtype=np.int32)
    
    # Create big-endian version
    arr_be = arr_native.astype('>i4')
    
    # Try to convert to ctypes
    try:
        ct_be = np.ctypeslib.as_ctypes(arr_be)
        arr_be2 = np.ctypeslib.as_array(ct_be)
        
        # Check if data is preserved correctly
        assert np.array_equal(arr_be, arr_be2), "Big-endian data not preserved"
    except NotImplementedError:
        # This might be expected
        pass
    
    # Create little-endian version
    arr_le = arr_native.astype('<i4')
    
    try:
        ct_le = np.ctypeslib.as_ctypes(arr_le)
        arr_le2 = np.ctypeslib.as_array(ct_le)
        
        # Check if data is preserved correctly
        assert np.array_equal(arr_le, arr_le2), "Little-endian data not preserved"
    except NotImplementedError:
        pass


# Test 3: Test with unusual but valid dtypes
@given(st.lists(st.integers(min_value=-128, max_value=127), min_size=1, max_size=10))
@settings(max_examples=200)
def test_uncommon_dtypes(values):
    """Test with less common but valid dtypes"""
    # Test with int8
    arr = np.array(values, dtype=np.int8)
    ct = np.ctypeslib.as_ctypes(arr)
    arr2 = np.ctypeslib.as_array(ct)
    assert np.array_equal(arr, arr2)
    
    # Test with float16 (half precision)
    arr_f16 = np.array(values, dtype=np.float16)
    try:
        ct_f16 = np.ctypeslib.as_ctypes(arr_f16)
        arr_f16_2 = np.ctypeslib.as_array(ct_f16)
        assert np.array_equal(arr_f16, arr_f16_2), "float16 not preserved"
    except NotImplementedError:
        # float16 might not be supported
        pass


# Test 4: Test with structured arrays containing padding
@given(st.integers(min_value=0, max_value=255),
       st.integers(min_value=-32768, max_value=32767))
@settings(max_examples=500)
def test_structured_with_padding(val1, val2):
    """Test structured arrays that might have padding"""
    # Create a dtype with potential padding
    dt = np.dtype([('a', np.uint8), ('b', np.int32)])
    
    arr = np.array([(val1, val2)], dtype=dt)
    
    # Convert to ctypes
    ct_type = np.ctypeslib.as_ctypes_type(dt)
    ct = np.ctypeslib.as_ctypes(arr)
    
    # Convert back
    arr2 = np.ctypeslib.as_array(ct)
    
    # Check values are preserved
    assert arr['a'][0] == arr2['a'][0], f"Field 'a' not preserved: {arr['a'][0]} != {arr2['a'][0]}"
    assert arr['b'][0] == arr2['b'][0], f"Field 'b' not preserved: {arr['b'][0]} != {arr2['b'][0]}"


# Test 5: Test ndpointer with shape parameter
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=6, max_size=6))
@settings(max_examples=200)
def test_ndpointer_shape_validation(values):
    """Test ndpointer's shape validation"""
    arr = np.array(values, dtype=np.float64).reshape((2, 3))
    
    # Create ndpointer with specific shape
    ptr_type = np.ctypeslib.ndpointer(dtype=np.float64, shape=(2, 3))
    
    # This should work
    result = ptr_type.from_param(arr)
    assert result is not None
    
    # Test with wrong shape - should fail
    arr_wrong = arr.reshape((3, 2))
    with pytest.raises(TypeError, match="shape"):
        ptr_type.from_param(arr_wrong)
    
    # Test with transposed array (different memory layout)
    arr_t = arr.T
    with pytest.raises(TypeError, match="shape"):
        ptr_type.from_param(arr_t)


# Test 6: Check handling of empty structured dtypes
def test_empty_structured_dtype():
    """Test conversion of empty structured dtypes"""
    # Create an empty structured dtype
    dt = np.dtype([])
    
    try:
        ct_type = np.ctypeslib.as_ctypes_type(dt)
        # If this works, check properties
        assert hasattr(ct_type, '_fields_')
    except (NotImplementedError, ValueError, KeyError) as e:
        # This might fail - that could be a bug
        print(f"Empty dtype conversion failed: {e}")


# Test 7: Test as_array with incorrect shape parameter
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20))
@settings(max_examples=200)
def test_as_array_shape_parameter(values):
    """Test as_array with shape parameter on ctypes arrays"""
    # Create ctypes array
    arr = np.array(values, dtype=np.int32)
    ct = np.ctypeslib.as_ctypes(arr)
    
    # as_array should ignore shape parameter for ctypes arrays
    # according to the docstring
    arr2 = np.ctypeslib.as_array(ct, shape=(9999,))  # Wrong shape should be ignored
    
    # Should get back original shape
    assert arr2.shape == arr.shape, f"Shape parameter should be ignored for ctypes arrays"


# Test 8: Test pointer type caching
def test_ndpointer_caching():
    """Test that ndpointer caches types correctly"""
    # Create two ndpointers with same parameters
    ptr1 = np.ctypeslib.ndpointer(dtype=np.float64, ndim=2)
    ptr2 = np.ctypeslib.ndpointer(dtype=np.float64, ndim=2)
    
    # They should be the same object (cached)
    assert ptr1 is ptr2, "ndpointer should cache types"
    
    # Different parameters should give different types
    ptr3 = np.ctypeslib.ndpointer(dtype=np.float32, ndim=2)
    assert ptr1 is not ptr3, "Different parameters should give different types"


# Test 9: Union types in structured arrays
def test_union_structured_arrays():
    """Test structured arrays that represent unions (overlapping fields)"""
    # Create a union-like dtype with overlapping fields
    dt = np.dtype({'names': ['x', 'y'], 'formats': [np.int32, np.float32], 'offsets': [0, 0]})
    
    arr = np.zeros(3, dtype=dt)
    arr['x'] = [1, 2, 3]
    
    # Convert to ctypes
    try:
        ct_type = np.ctypeslib.as_ctypes_type(dt)
        assert issubclass(ct_type, ctypes.Union), "Overlapping fields should create Union"
        
        ct = np.ctypeslib.as_ctypes(arr)
        arr2 = np.ctypeslib.as_array(ct)
        
        # Since it's a union, the int32 and float32 interpretations of the same memory
        # Check that at least the memory layout is preserved
        assert arr.nbytes == arr2.nbytes
    except Exception as e:
        print(f"Union conversion issue: {e}")


# Test 10: Test with object dtype (should fail)
def test_object_dtype_fails():
    """Test that object dtypes are properly rejected"""
    arr = np.array([None, 'test', 123], dtype=object)
    
    with pytest.raises(NotImplementedError):
        np.ctypeslib.as_ctypes_type(np.dtype(object))
    
    with pytest.raises(NotImplementedError):
        np.ctypeslib.as_ctypes(arr)


if __name__ == "__main__":
    print("Running targeted bug-finding tests...")
    
    # Run all tests
    test_f_contiguous_round_trip()
    test_endianness_handling()
    test_uncommon_dtypes()
    test_structured_with_padding()
    test_ndpointer_shape_validation()
    test_empty_structured_dtype()
    test_as_array_shape_parameter()
    test_ndpointer_caching()
    test_union_structured_arrays()
    test_object_dtype_fails()
    
    print("Tests completed!")