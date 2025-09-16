import numpy as np
import ctypes
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


# Strategy for generating valid numpy dtypes
valid_dtypes = st.sampled_from([
    np.int8, np.int16, np.int32, np.int64,
    np.uint8, np.uint16, np.uint32, np.uint64,
    np.float32, np.float64,
    np.bool_,
    np.complex64, np.complex128,
])

# Strategy for generating valid array shapes
array_shapes = st.lists(st.integers(min_value=1, max_value=10), min_size=0, max_size=3)

# Strategy for generating contiguous numpy arrays
@st.composite
def contiguous_arrays(draw):
    dtype = draw(valid_dtypes)
    shape = tuple(draw(array_shapes))
    
    if shape == ():
        # Scalar
        if dtype in [np.complex64, np.complex128]:
            real = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
            imag = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
            value = complex(real, imag)
        elif dtype == np.bool_:
            value = draw(st.booleans())
        elif np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype)
            value = draw(st.integers(min_value=int(info.min), max_value=int(info.max)))
        else:  # float
            value = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
        arr = np.array(value, dtype=dtype)
    else:
        # Generate appropriate values based on dtype
        size = int(np.prod(shape)) if shape else 1
        if dtype in [np.complex64, np.complex128]:
            real_vals = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=size, max_size=size))
            imag_vals = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=size, max_size=size))
            values = [complex(r, i) for r, i in zip(real_vals, imag_vals)]
        elif dtype == np.bool_:
            values = draw(st.lists(st.booleans(), min_size=size, max_size=size))
        elif np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype)
            values = draw(st.lists(st.integers(min_value=int(info.min), max_value=int(info.max)), min_size=size, max_size=size))
        else:  # float
            values = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=size, max_size=size))
        
        arr = np.array(values, dtype=dtype).reshape(shape)
    
    # Ensure array is contiguous
    if not (arr.flags['C_CONTIGUOUS'] or arr.flags['F_CONTIGUOUS']):
        arr = np.ascontiguousarray(arr)
    
    return arr


# Property 1: Round-trip property for as_ctypes/as_array
@given(contiguous_arrays())
@settings(max_examples=1000)
def test_as_ctypes_as_array_round_trip(arr):
    """Test that as_array(as_ctypes(arr)) preserves the array data"""
    # Skip complex types as they're not supported by ctypes
    if arr.dtype in [np.complex64, np.complex128]:
        assume(False)
    
    # Convert to ctypes
    try:
        ct = np.ctypeslib.as_ctypes(arr)
    except NotImplementedError:
        # Some dtypes might not be supported
        assume(False)
        return
    
    # Convert back to numpy
    arr2 = np.ctypeslib.as_array(ct)
    
    # Check that arrays are equal
    assert arr.shape == arr2.shape, f"Shape mismatch: {arr.shape} != {arr2.shape}"
    assert arr.dtype == arr2.dtype, f"Dtype mismatch: {arr.dtype} != {arr2.dtype}"
    assert np.array_equal(arr, arr2), "Array values not equal after round-trip"
    
    # They should share memory
    assert arr.__array_interface__['data'][0] == arr2.__array_interface__['data'][0], "Arrays don't share memory"


# Property 2: as_ctypes_type round-trip
@given(valid_dtypes)
@settings(max_examples=500)
def test_as_ctypes_type_round_trip(dtype):
    """Test dtype -> ctypes type -> dtype conversion"""
    # Skip complex types as they're not supported
    if dtype in [np.complex64, np.complex128]:
        assume(False)
    
    try:
        ctype = np.ctypeslib.as_ctypes_type(dtype)
        # Create an instance and convert back
        if hasattr(ctype, '_type_'):
            # It's a pointer type
            dtype2 = np.dtype(ctype._type_)
        else:
            dtype2 = np.dtype(ctype)
        
        # Check compatibility (they might not be exactly equal due to dtype normalization)
        assert np.can_cast(dtype, dtype2) and np.can_cast(dtype2, dtype), \
            f"Dtypes not compatible: {dtype} vs {dtype2}"
    except (NotImplementedError, TypeError):
        # Some dtypes might not be supported
        pass


# Property 3: ndpointer type checking
@given(contiguous_arrays(), 
       st.one_of(st.none(), valid_dtypes),
       st.one_of(st.none(), st.integers(min_value=0, max_value=5)))
@settings(max_examples=500)
def test_ndpointer_type_checking(arr, expected_dtype, expected_ndim):
    """Test that ndpointer correctly validates arrays"""
    # Skip complex types
    if arr.dtype in [np.complex64, np.complex128]:
        assume(False)
    if expected_dtype in [np.complex64, np.complex128]:
        assume(False)
    
    # Create ndpointer type
    ptr_type = np.ctypeslib.ndpointer(dtype=expected_dtype, ndim=expected_ndim)
    
    # Test from_param
    should_pass = True
    if expected_dtype is not None and arr.dtype != expected_dtype:
        should_pass = False
    if expected_ndim is not None and arr.ndim != expected_ndim:
        should_pass = False
    
    if should_pass:
        result = ptr_type.from_param(arr)
        assert result is not None
    else:
        with pytest.raises(TypeError):
            ptr_type.from_param(arr)


# Property 4: Structured dtypes
@given(st.lists(
    st.tuples(
        st.text(alphabet=st.characters(whitelist_categories=['Ll', 'Lu']), min_size=1, max_size=10),
        st.sampled_from(['i1', 'i2', 'i4', 'i8', 'u1', 'u2', 'u4', 'u8', 'f4', 'f8'])
    ),
    min_size=1,
    max_size=5,
    unique_by=lambda x: x[0]  # Unique field names
))
@settings(max_examples=200)
def test_structured_dtype_conversion(fields):
    """Test conversion of structured dtypes to ctypes"""
    # Create structured dtype
    dtype = np.dtype(fields)
    
    try:
        # Convert to ctypes type
        ctype = np.ctypeslib.as_ctypes_type(dtype)
        
        # Check that it's a Structure
        assert issubclass(ctype, ctypes.Structure), "Should create a ctypes.Structure"
        
        # Check fields are preserved (though order might change)
        ctype_fields = {name for name, _ in ctype._fields_ if name}
        dtype_fields = set(dtype.names)
        assert dtype_fields.issubset(ctype_fields), f"Missing fields: {dtype_fields - ctype_fields}"
        
    except NotImplementedError:
        # Some structured dtypes might not be supported
        pass


# Property 5: Zero-sized arrays
@given(st.integers(min_value=1, max_value=3))
@settings(max_examples=100)
def test_zero_sized_arrays(ndim):
    """Test handling of zero-sized arrays"""
    # Create shape with at least one zero dimension
    shape = [1] * ndim
    shape[0] = 0  # Make first dimension 0
    shape = tuple(shape)
    
    arr = np.zeros(shape, dtype=np.int32)
    
    # as_ctypes should handle zero-sized arrays
    ct = np.ctypeslib.as_ctypes(arr)
    arr2 = np.ctypeslib.as_array(ct)
    
    assert arr.shape == arr2.shape, f"Shape mismatch for zero-sized array: {arr.shape} != {arr2.shape}"
    assert arr.size == arr2.size == 0, "Size should be 0"


# Property 6: Memory sharing verification
@given(contiguous_arrays())
@settings(max_examples=500)
def test_memory_sharing(arr):
    """Test that as_ctypes creates a view that shares memory"""
    # Skip complex types
    if arr.dtype in [np.complex64, np.complex128]:
        assume(False)
    
    try:
        ct = np.ctypeslib.as_ctypes(arr)
        
        # Modify the original array
        if arr.size > 0:
            flat_idx = 0
            if np.issubdtype(arr.dtype, np.integer):
                old_val = arr.flat[flat_idx]
                new_val = (old_val + 1) % np.iinfo(arr.dtype).max
                arr.flat[flat_idx] = new_val
                
                # Check that ctypes object reflects the change
                if hasattr(ct, '__getitem__'):
                    if arr.ndim == 1:
                        assert ct[flat_idx] == new_val, "Memory not shared: ctypes object doesn't reflect change"
                    
                # Convert back and verify
                arr2 = np.ctypeslib.as_array(ct)
                assert arr2.flat[flat_idx] == new_val, "Memory not shared: converted array doesn't reflect change"
                
    except (NotImplementedError, TypeError, AttributeError):
        # Some operations might not be supported
        pass


# Property 7: Test readonly arrays should fail
@given(contiguous_arrays())
@settings(max_examples=200)
def test_readonly_arrays_fail(arr):
    """Test that as_ctypes correctly rejects readonly arrays"""
    # Skip complex types
    if arr.dtype in [np.complex64, np.complex128]:
        assume(False)
        
    # Make array readonly
    arr.flags.writeable = False
    
    # Should raise TypeError
    with pytest.raises(TypeError, match="readonly"):
        np.ctypeslib.as_ctypes(arr)


# Property 8: Edge case - scalar arrays
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
@settings(max_examples=200)
def test_scalar_arrays(value):
    """Test conversion of 0-dimensional (scalar) arrays"""
    arr = np.array(value, dtype=np.float64)
    assert arr.shape == ()
    
    ct = np.ctypeslib.as_ctypes(arr)
    arr2 = np.ctypeslib.as_array(ct)
    
    assert arr.shape == arr2.shape == (), "Shape should remain ()"
    assert math.isclose(float(arr), float(arr2), rel_tol=1e-9), "Scalar value not preserved"


if __name__ == "__main__":
    # Run all tests
    print("Running property-based tests for numpy.ctypeslib...")
    test_as_ctypes_as_array_round_trip()
    test_as_ctypes_type_round_trip()
    test_ndpointer_type_checking()
    test_structured_dtype_conversion()
    test_zero_sized_arrays()
    test_memory_sharing()
    test_readonly_arrays_fail()
    test_scalar_arrays()
    print("All tests completed!")