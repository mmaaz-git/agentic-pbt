"""
Property-based tests for numpy.lib dtype conversion functions.
Testing round-trip property: descr_to_dtype(dtype_to_descr(dt)) should equal dt
"""

import numpy as np
from numpy.lib.format import dtype_to_descr, descr_to_dtype
from hypothesis import given, strategies as st, settings, assume
import warnings


# Strategy for generating numpy dtypes
@st.composite
def numpy_dtypes(draw):
    """Generate various numpy dtypes for testing."""
    
    # Basic scalar dtypes
    basic_dtypes = [
        np.dtype('bool'),
        np.dtype('int8'), np.dtype('int16'), np.dtype('int32'), np.dtype('int64'),
        np.dtype('uint8'), np.dtype('uint16'), np.dtype('uint32'), np.dtype('uint64'),
        np.dtype('float16'), np.dtype('float32'), np.dtype('float64'),
        np.dtype('complex64'), np.dtype('complex128'),
    ]
    
    # Endianness variations
    endian_prefixes = ['<', '>', '=', '|']
    endian_dtypes = []
    for prefix in endian_prefixes:
        for basic_type in ['i1', 'i2', 'i4', 'i8', 'u1', 'u2', 'u4', 'u8', 'f2', 'f4', 'f8']:
            try:
                endian_dtypes.append(np.dtype(prefix + basic_type))
            except:
                pass
    
    # Structured dtypes
    field_names = draw(st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'), 
                                 min_size=1, max_size=5, unique=True))
    field_types = draw(st.lists(st.sampled_from(basic_dtypes), 
                                min_size=len(field_names), max_size=len(field_names)))
    
    structured_dtype = np.dtype([(name, dtype) for name, dtype in zip(field_names, field_types)])
    
    # String and bytes dtypes
    string_dtypes = [
        np.dtype('S10'),  # Fixed-size bytes
        np.dtype('U10'),  # Fixed-size unicode
        np.dtype(f'S{draw(st.integers(1, 100))}'),
        np.dtype(f'U{draw(st.integers(1, 100))}'),
    ]
    
    # Choose which type to generate
    dtype_choice = draw(st.sampled_from(
        basic_dtypes + endian_dtypes + [structured_dtype] + string_dtypes
    ))
    
    return dtype_choice


@given(dtype=numpy_dtypes())
@settings(max_examples=500)
def test_dtype_round_trip(dtype):
    """Test that dtype_to_descr and descr_to_dtype are inverse operations."""
    
    # Suppress warnings about metadata
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        
        # Convert dtype to descriptor
        descr = dtype_to_descr(dtype)
        
        # Convert back to dtype
        reconstructed_dtype = descr_to_dtype(descr)
        
        # They should be equal
        assert reconstructed_dtype == dtype, \
            f"Round-trip failed: {dtype} -> {descr} -> {reconstructed_dtype}"


@given(dtype=numpy_dtypes())
@settings(max_examples=200)
def test_dtype_descr_preserves_itemsize(dtype):
    """Test that the round-trip preserves itemsize."""
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        
        descr = dtype_to_descr(dtype)
        reconstructed = descr_to_dtype(descr)
        
        assert reconstructed.itemsize == dtype.itemsize, \
            f"Itemsize changed: {dtype.itemsize} -> {reconstructed.itemsize}"


@given(dtype=numpy_dtypes())
@settings(max_examples=200)
def test_dtype_descr_preserves_byteorder(dtype):
    """Test that the round-trip preserves byte order when applicable."""
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        
        descr = dtype_to_descr(dtype)
        reconstructed = descr_to_dtype(descr)
        
        # For dtypes that have a meaningful byte order
        if hasattr(dtype, 'byteorder') and dtype.byteorder in '<>=':
            assert reconstructed.byteorder == dtype.byteorder, \
                f"Byteorder changed: {dtype.byteorder} -> {reconstructed.byteorder}"


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])