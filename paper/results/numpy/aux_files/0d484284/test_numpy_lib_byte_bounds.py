"""
Property-based tests for numpy.lib.array_utils.byte_bounds.
Testing invariants about memory bounds.
"""

import numpy as np
from numpy.lib.array_utils import byte_bounds
from hypothesis import given, strategies as st, settings, assume


@st.composite
def numpy_arrays(draw):
    """Generate various numpy arrays for testing."""
    
    # Generate shape
    ndim = draw(st.integers(0, 4))
    if ndim == 0:
        shape = ()
    else:
        shape = draw(st.lists(st.integers(1, 10), min_size=ndim, max_size=ndim))
    
    # Generate dtype
    dtype = draw(st.sampled_from([
        np.int8, np.int16, np.int32, np.int64,
        np.uint8, np.uint16, np.uint32, np.uint64,
        np.float16, np.float32, np.float64,
        np.complex64, np.complex128,
        bool
    ]))
    
    # Generate array
    size = int(np.prod(shape)) if shape else 1  # Convert to Python int
    
    if dtype == bool:
        data = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    elif np.issubdtype(dtype, np.integer):
        info = np.iinfo(dtype)
        data = draw(st.lists(st.integers(int(info.min), int(info.max)), min_size=size, max_size=size))
    elif np.issubdtype(dtype, np.floating):
        data = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, 
                                       min_value=-1e10, max_value=1e10), 
                            min_size=size, max_size=size))
    else:  # complex
        real = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                                       min_value=-1e10, max_value=1e10),
                            min_size=size, max_size=size))
        imag = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                                       min_value=-1e10, max_value=1e10),
                            min_size=size, max_size=size))
        data = [complex(r, i) for r, i in zip(real, imag)]
    
    arr = np.array(data, dtype=dtype)
    if shape:
        arr = arr.reshape(shape)
    
    return arr


@given(arr=numpy_arrays())
@settings(max_examples=200)
def test_byte_bounds_basic_invariant(arr):
    """Test that byte_bounds returns valid bounds."""
    
    low, high = byte_bounds(arr)
    
    # Basic checks
    assert isinstance(low, int), f"low should be int, got {type(low)}"
    assert isinstance(high, int), f"high should be int, got {type(high)}"
    assert low <= high, f"low ({low}) should be <= high ({high})"
    
    # The range should be at least as large as the array's byte size
    # For contiguous arrays, it should be exactly the size
    if arr.flags['C_CONTIGUOUS'] or arr.flags['F_CONTIGUOUS']:
        expected_size = arr.size * arr.itemsize
        actual_size = high - low
        assert actual_size == expected_size, \
            f"Contiguous array size mismatch: expected {expected_size}, got {actual_size}"


@given(arr=numpy_arrays())
@settings(max_examples=200)
def test_byte_bounds_slice_relationship(arr):
    """Test that sliced arrays have bounds within parent bounds."""
    
    if arr.ndim == 0 or arr.size == 0:
        return  # Skip scalar and empty arrays
    
    parent_low, parent_high = byte_bounds(arr)
    
    # Take various slices
    if arr.ndim == 1 and len(arr) > 1:
        slice_arr = arr[::2]  # Every other element
        slice_low, slice_high = byte_bounds(slice_arr)
        
        # Slice bounds should be within parent bounds
        assert slice_low >= parent_low, \
            f"Slice low bound {slice_low} < parent low {parent_low}"
        assert slice_high <= parent_high, \
            f"Slice high bound {slice_high} > parent high {parent_high}"


@given(arr=numpy_arrays())
@settings(max_examples=200)
def test_byte_bounds_view_consistency(arr):
    """Test that views have consistent bounds."""
    
    if arr.size == 0:
        return
    
    # Create a view with same data
    view = arr.view()
    
    arr_low, arr_high = byte_bounds(arr)
    view_low, view_high = byte_bounds(view)
    
    # Views of the same data should have the same bounds
    assert arr_low == view_low, f"View has different low bound"
    assert arr_high == view_high, f"View has different high bound"


@given(
    shape=st.lists(st.integers(1, 10), min_size=2, max_size=3),
    dtype=st.sampled_from([np.int32, np.float64])
)
@settings(max_examples=100)
def test_byte_bounds_transpose_invariant(shape, dtype):
    """Test that transposed arrays maintain valid bounds."""
    
    arr = np.arange(np.prod(shape), dtype=dtype).reshape(shape)
    transposed = arr.T
    
    arr_low, arr_high = byte_bounds(arr)
    trans_low, trans_high = byte_bounds(transposed)
    
    # Transposed array uses the same memory
    assert trans_low == arr_low, f"Transpose changed low bound"
    assert trans_high == arr_high, f"Transpose changed high bound"
    
    # But it's not contiguous anymore (unless it's 1D or has a dimension of size 1)
    if arr.ndim > 1 and all(s > 1 for s in arr.shape):
        assert not transposed.flags['C_CONTIGUOUS'], "Transpose should not be C-contiguous"


@given(arr=numpy_arrays())
@settings(max_examples=100)
def test_byte_bounds_negative_stride(arr):
    """Test byte_bounds with negative strides (reversed arrays)."""
    
    if arr.size <= 1:
        return
    
    # Reverse the array
    reversed_arr = arr[::-1] if arr.ndim == 1 else arr[::-1, ...]
    
    orig_low, orig_high = byte_bounds(arr)
    rev_low, rev_high = byte_bounds(reversed_arr)
    
    # Reversed array uses same memory range
    assert rev_low == orig_low, f"Reverse changed low bound"
    assert rev_high == orig_high, f"Reverse changed high bound"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])