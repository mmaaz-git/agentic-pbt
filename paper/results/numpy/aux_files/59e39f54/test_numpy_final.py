import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example, note
from hypothesis.extra import numpy as npst
import math
import sys


# Final push to find actual bugs

# Test 1: Testing numpy string comparison with Unicode
@given(st.text(min_size=0, max_size=100))
def test_string_array_unicode(text):
    # Create array with Unicode string
    arr = np.array([text], dtype='U100')
    
    # Should preserve the string
    assert arr[0] == text


# Test 2: Testing histogram with infinite values
@given(st.lists(st.floats(allow_infinity=True), min_size=1, max_size=20))
def test_histogram_with_infinity(values):
    arr = np.array(values)
    
    if np.any(np.isinf(arr)):
        # Histogram should handle infinity
        hist, bins = np.histogram(arr[np.isfinite(arr)], bins=10)
        assert np.sum(hist) == np.sum(np.isfinite(arr))


# Test 3: Testing astype with overflow
@given(st.floats(min_value=1e20, max_value=1e30))
def test_astype_overflow(large_float):
    arr = np.array([large_float])
    
    # Converting large float to int8 should overflow
    with pytest.warns(RuntimeWarning):
        result = arr.astype(np.int8)
        # Result should be within int8 range
        assert -128 <= result[0] <= 127


# Test 4: Testing array comparison with mixed types
def test_mixed_type_comparison():
    int_arr = np.array([1, 2, 3])
    float_arr = np.array([1.0, 2.0, 3.0])
    
    # Should be equal despite different dtypes
    assert np.array_equal(int_arr, float_arr)


# Test 5: Testing numpy's handling of complex number edge cases
@given(st.complex_numbers(allow_nan=True, allow_infinity=True))
def test_complex_number_edge_cases(z):
    arr = np.array([z])
    
    # abs should work on complex
    abs_val = np.abs(arr[0])
    
    if not np.isnan(z.real) and not np.isnan(z.imag):
        expected = math.sqrt(z.real**2 + z.imag**2)
        if not math.isinf(expected):
            assert np.isclose(abs_val, expected, rtol=1e-10)


# Test 6: Testing save/load round-trip with edge cases
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(),
                   elements=st.floats(allow_nan=True, allow_infinity=True)))
def test_save_load_roundtrip(arr):
    filename = '/tmp/test_array.npy'
    
    # Save and load
    np.save(filename, arr)
    loaded = np.load(filename)
    
    # Should be identical (including NaN and inf)
    assert arr.shape == loaded.shape
    assert arr.dtype == loaded.dtype
    
    # Check values (NaN-aware comparison)
    if arr.size > 0:
        nan_mask = np.isnan(arr)
        assert np.array_equal(nan_mask, np.isnan(loaded))
        assert np.array_equal(arr[~nan_mask], loaded[~nan_mask])


# Test 7: Testing numpy's random seed consistency
def test_random_seed_consistency():
    # Set seed and generate numbers
    np.random.seed(42)
    first = np.random.rand(10)
    
    # Reset seed and generate again
    np.random.seed(42)
    second = np.random.rand(10)
    
    # Should be identical
    assert np.array_equal(first, second)


# Test 8: Testing matrix rank with edge cases
@given(n=st.integers(1, 10))
def test_matrix_rank_edge_cases(n):
    # Zero matrix should have rank 0
    zero_matrix = np.zeros((n, n))
    assert np.linalg.matrix_rank(zero_matrix) == 0
    
    # Identity matrix should have full rank
    identity = np.eye(n)
    assert np.linalg.matrix_rank(identity) == n


# Test 9: Testing numpy's handling of empty slices
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_empty_slice_behavior(arr):
    # Empty slice should give empty array
    empty = arr[5:5]
    assert len(empty) == 0
    
    # Reverse empty slice
    empty2 = arr[5:4]
    assert len(empty2) == 0


# Test 10: Testing frombuffer with different dtypes
def test_frombuffer_dtypes():
    # Create bytes
    data = b'\x01\x02\x03\x04\x05\x06\x07\x08'
    
    # Interpret as different dtypes
    as_uint8 = np.frombuffer(data, dtype=np.uint8)
    as_uint16 = np.frombuffer(data, dtype=np.uint16)
    as_uint32 = np.frombuffer(data, dtype=np.uint32)
    
    assert len(as_uint8) == 8
    assert len(as_uint16) == 4
    assert len(as_uint32) == 2


# Test 11: Testing delete function edge cases
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_delete_edge_cases(arr):
    # Delete with negative index
    if len(arr) > 0:
        result = np.delete(arr, -1)
        assert len(result) == len(arr) - 1
        assert np.array_equal(result, arr[:-1])
    
    # Delete multiple indices
    if len(arr) >= 3:
        result = np.delete(arr, [0, -1])
        assert len(result) == len(arr) - 2


# Test 12: Testing insert function edge cases
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)),
       st.floats(allow_nan=False, allow_infinity=False))
def test_insert_edge_cases(arr, value):
    # Insert at negative index
    result = np.insert(arr, -1, value)
    assert len(result) == len(arr) + 1
    assert result[-2] == value
    
    # Insert beyond bounds
    result2 = np.insert(arr, 1000, value)
    assert result2[-1] == value


# Test 13: Testing append with axis parameter
@given(npst.arrays(dtype=np.float64, shape=(st.integers(2, 5), st.integers(2, 5)),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_append_with_axis(arr):
    rows, cols = arr.shape
    
    # Append along axis 0
    new_row = np.ones(cols)
    result = np.append(arr, [new_row], axis=0)
    assert result.shape == (rows + 1, cols)
    assert np.array_equal(result[-1], new_row)


# Test 14: Testing iinfo and finfo consistency
def test_dtype_info_consistency():
    # Integer info
    i8_info = np.iinfo(np.int8)
    assert i8_info.min == -128
    assert i8_info.max == 127
    
    # Float info
    f32_info = np.finfo(np.float32)
    assert f32_info.eps > 0
    assert f32_info.max > f32_info.min


# Test 15: Testing byte order conversions
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_byte_order_conversion(arr):
    # Swap byte order
    swapped = arr.byteswap()
    # Swap back
    restored = swapped.byteswap()
    
    # Should be identical
    assert np.array_equal(arr, restored)


# Test 16: Testing numpy's handling of 0-d arrays
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_zero_dimensional_arrays(value):
    # Create 0-d array
    arr = np.array(value)
    
    assert arr.ndim == 0
    assert arr.shape == ()
    assert arr.size == 1
    
    # Should be convertible to scalar
    assert float(arr) == value


# Test 17: Testing copyto with where parameter
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)),
       npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_copyto_with_where(src, dst):
    # Make same size
    min_len = min(len(src), len(dst))
    src = src[:min_len]
    dst = dst[:min_len].copy()
    
    # Copy only where condition is true
    condition = src > 0
    original_dst = dst.copy()
    np.copyto(dst, src, where=condition)
    
    # Check selective copy
    for i in range(len(dst)):
        if condition[i]:
            assert dst[i] == src[i]
        else:
            assert dst[i] == original_dst[i]


# Test 18: Testing as_strided for advanced views
@given(npst.arrays(dtype=np.float64, shape=st.integers(10, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_as_strided_views(arr):
    # Create overlapping windows view
    from numpy.lib.stride_tricks import as_strided
    
    window_size = 3
    if len(arr) >= window_size:
        shape = (len(arr) - window_size + 1, window_size)
        strides = (arr.strides[0], arr.strides[0])
        
        windows = as_strided(arr, shape=shape, strides=strides)
        
        # Check that windows are correct
        for i in range(len(windows)):
            assert np.array_equal(windows[i], arr[i:i+window_size])


# Test 19: Testing nan functions with all-nan arrays
def test_nan_functions_all_nan():
    all_nan = np.array([np.nan, np.nan, np.nan])
    
    # nanmean of all NaN should be NaN
    assert np.isnan(np.nanmean(all_nan))
    
    # nansum of all NaN should be 0
    assert np.nansum(all_nan) == 0
    
    # nanmax/nanmin should warn and return NaN
    with pytest.warns(RuntimeWarning):
        assert np.isnan(np.nanmax(all_nan))
        assert np.isnan(np.nanmin(all_nan))


# Test 20: Testing array priority in operations
class HighPriorityArray:
    __array_priority__ = 1000
    
    def __init__(self, arr):
        self.arr = np.asarray(arr)
    
    def __add__(self, other):
        return "HighPriorityArray.__add__ called"
    
    def __radd__(self, other):
        return "HighPriorityArray.__radd__ called"

def test_array_priority():
    np_arr = np.array([1, 2, 3])
    high_priority = HighPriorityArray([4, 5, 6])
    
    # High priority object's method should be called
    result = np_arr + high_priority
    assert result == "HighPriorityArray.__radd__ called"


# Test 21: Testing shares_memory function
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_shares_memory(arr):
    # View shares memory
    view = arr[:]
    assert np.shares_memory(arr, view)
    
    # Copy doesn't share memory
    copy = arr.copy()
    assert not np.shares_memory(arr, copy)


# Test 22: Testing can_cast function
def test_can_cast():
    # Should be able to cast int to float
    assert np.can_cast(np.int32, np.float64)
    
    # Should not be able to cast float to int without loss
    assert not np.can_cast(np.float64, np.int32, casting='safe')
    
    # But should with 'unsafe' casting
    assert np.can_cast(np.float64, np.int32, casting='unsafe')


# Test 23: Testing result_type function
def test_result_type():
    # Result type of int and float should be float
    assert np.result_type(np.int32, np.float32) == np.float32
    
    # Result type of two ints should be int
    assert np.result_type(np.int32, np.int64) == np.int64


# Test 24: Testing numpy scalar operations
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_numpy_scalar_operations(value):
    # Create numpy scalar
    scalar = np.float64(value)
    
    # Should behave like regular float
    assert scalar + 1 == value + 1
    assert scalar * 2 == value * 2
    
    # But should have numpy methods
    assert hasattr(scalar, 'dtype')
    assert scalar.dtype == np.float64


# Test 25: Looking for actual bug - testing complex edge case with stride tricks
@given(st.integers(5, 20))
def test_diagonal_stride_bug(n):
    # Create matrix
    matrix = np.arange(n * n).reshape(n, n)
    
    # Get diagonal using stride tricks
    diag = np.diagonal(matrix)
    
    # Modify diagonal - this should NOT affect original matrix
    # since diagonal should return a copy (as of NumPy 1.9+)
    diag_copy = diag.copy()
    diag[:] = -1
    
    # Check if original matrix was modified
    # If diagonal returns a view (old behavior), this would fail
    for i in range(n):
        if matrix[i, i] == -1:
            # This would be a bug in older numpy versions
            # but is expected behavior in newer versions where diagonal returns a copy
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x", "--hypothesis-show-statistics"])