import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.extra import numpy as npst
import math
import sys


# Test edge cases more aggressively

# Test 1: Testing einsum consistency
@given(npst.arrays(dtype=np.float64, shape=(st.integers(1, 5), st.integers(1, 5)),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_einsum_trace_consistency(matrix):
    # Make it square
    n = min(matrix.shape)
    matrix = matrix[:n, :n]
    
    # einsum trace should equal np.trace
    einsum_trace = np.einsum('ii->', matrix)
    regular_trace = np.trace(matrix)
    
    assert np.isclose(einsum_trace, regular_trace, rtol=1e-10)


# Test 2: Testing polyfit/polyval round-trip
@given(npst.arrays(dtype=np.float64, shape=st.integers(3, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)),
       st.integers(1, 3))
def test_polyfit_polyval_roundtrip(y, deg):
    x = np.arange(len(y), dtype=np.float64)
    
    # Fit polynomial
    coeffs = np.polyfit(x, y, deg)
    
    # Evaluate at same points
    y_reconstructed = np.polyval(coeffs, x)
    
    # Should be close for low degree polynomials
    if deg < len(y):
        assert np.allclose(y_reconstructed, y, rtol=1e-5, atol=1e-5)


# Test 3: Testing FFT inverse
@given(npst.arrays(dtype=np.complex128, shape=st.integers(1, 100),
                   elements=st.complex_numbers(allow_nan=False, allow_infinity=False, 
                                              min_magnitude=0, max_magnitude=100)))
def test_fft_ifft_inverse(arr):
    fft_result = np.fft.fft(arr)
    reconstructed = np.fft.ifft(fft_result)
    assert np.allclose(reconstructed, arr, rtol=1e-10, atol=1e-10)


# Test 4: Testing real FFT properties
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_rfft_irfft_inverse(arr):
    rfft_result = np.fft.rfft(arr)
    reconstructed = np.fft.irfft(rfft_result, n=len(arr))
    assert np.allclose(reconstructed, arr, rtol=1e-10, atol=1e-10)


# Test 5: Testing convolve properties
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_convolve_with_identity(arr):
    # Convolving with [1] should give same array
    identity = np.array([1.0])
    result = np.convolve(arr, identity, mode='same')
    assert np.allclose(result, arr, rtol=1e-10)


# Test 6: Testing correlate properties  
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_correlate_with_self(arr):
    # Auto-correlation at zero lag should be sum of squares
    if len(arr) > 0:
        auto_corr = np.correlate(arr, arr, mode='valid')
        expected = np.sum(arr * arr)
        assert np.isclose(auto_corr[0], expected, rtol=1e-10)


# Test 7: Testing gradient consistency
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 50),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_gradient_diff_consistency(arr):
    # For 1D arrays, gradient should be similar to diff
    grad = np.gradient(arr)
    
    # Check middle elements (gradient uses central differences)
    for i in range(1, len(arr) - 1):
        expected = (arr[i+1] - arr[i-1]) / 2.0
        assert np.isclose(grad[i], expected, rtol=1e-10)


# Test 8: Testing searchsorted consistency
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 50),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
def test_searchsorted_consistency(arr, value):
    sorted_arr = np.sort(arr)
    idx = np.searchsorted(sorted_arr, value)
    
    # Value should be >= all elements before idx
    # and < all elements from idx onward (or equal if right side)
    if idx > 0:
        assert sorted_arr[idx-1] <= value or np.isclose(sorted_arr[idx-1], value)
    if idx < len(sorted_arr):
        assert sorted_arr[idx] >= value or np.isclose(sorted_arr[idx], value)


# Test 9: Testing allclose symmetry
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)),
       npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)))
def test_allclose_symmetry(a, b):
    # Make same shape
    if a.shape != b.shape:
        return  # Skip incompatible shapes
    
    # allclose should be symmetric
    result1 = np.allclose(a, b)
    result2 = np.allclose(b, a)
    assert result1 == result2


# Test 10: Testing array_equal reflexivity
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=3),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_array_equal_reflexivity(arr):
    # Array should equal itself
    assert np.array_equal(arr, arr)


# Test 11: Testing cross product properties for 3D vectors
@given(npst.arrays(dtype=np.float64, shape=3,
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)),
       npst.arrays(dtype=np.float64, shape=3,
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_cross_product_perpendicular(a, b):
    cross = np.cross(a, b)
    
    # Cross product should be perpendicular to both vectors
    # (unless they're parallel)
    if not np.allclose(cross, 0):
        dot_a = np.dot(cross, a)
        dot_b = np.dot(cross, b)
        assert np.isclose(dot_a, 0, atol=1e-10)
        assert np.isclose(dot_b, 0, atol=1e-10)


# Test 12: Testing linspace endpoint consistency
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
       st.integers(2, 100))
def test_linspace_endpoints(start, stop, num):
    arr = np.linspace(start, stop, num)
    
    # First and last elements should match start and stop
    assert np.isclose(arr[0], start, rtol=1e-10)
    assert np.isclose(arr[-1], stop, rtol=1e-10)
    assert len(arr) == num


# Test 13: Testing logspace properties
@given(st.floats(min_value=-5, max_value=5),
       st.floats(min_value=-5, max_value=5),
       st.integers(2, 50))
def test_logspace_log_property(start, stop, num):
    if start > stop:
        start, stop = stop, start
    
    arr = np.logspace(start, stop, num)
    
    # Taking log10 should give linear spacing
    log_arr = np.log10(arr)
    
    # Check that it's approximately linearly spaced
    diffs = np.diff(log_arr)
    if len(diffs) > 0:
        expected_diff = (stop - start) / (num - 1)
        assert np.allclose(diffs, expected_diff, rtol=1e-5)


# Test 14: Testing meshgrid consistency
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)),
       npst.arrays(dtype=np.float64, shape=st.integers(2, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_meshgrid_shape(x, y):
    X, Y = np.meshgrid(x, y)
    
    # Check shapes
    assert X.shape == (len(y), len(x))
    assert Y.shape == (len(y), len(x))
    
    # Check values
    for i in range(len(y)):
        assert np.array_equal(X[i, :], x)
    for j in range(len(x)):
        assert np.array_equal(Y[:, j], y)


# Test 15: Testing rot90 four times gives original
@given(npst.arrays(dtype=np.float64, shape=(st.integers(2, 10), st.integers(2, 10)),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_rot90_four_times(arr):
    # Rotating 4 times by 90 degrees should give original
    rotated = np.rot90(np.rot90(np.rot90(np.rot90(arr))))
    assert np.array_equal(rotated, arr)


# Test 16: Testing flip twice gives original
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=3),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_flip_twice(arr):
    # Flipping twice should give original
    flipped = np.flip(np.flip(arr))
    assert np.array_equal(flipped, arr)


# Test 17: Testing isnan consistency
@given(st.lists(st.one_of(st.floats(allow_nan=True, allow_infinity=False),
                          st.just(float('nan'))), min_size=1, max_size=10))
def test_isnan_consistency(lst):
    arr = np.array(lst)
    
    for i, val in enumerate(lst):
        if math.isnan(val):
            assert np.isnan(arr[i])
        else:
            assert not np.isnan(arr[i])


# Test 18: Testing isinf consistency  
@given(st.lists(st.one_of(st.floats(allow_infinity=True),
                          st.just(float('inf')),
                          st.just(float('-inf'))), min_size=1, max_size=10))
def test_isinf_consistency(lst):
    arr = np.array(lst)
    
    for i, val in enumerate(lst):
        if math.isinf(val):
            assert np.isinf(arr[i])
        else:
            assert not np.isinf(arr[i])


# Test 19: Testing sign properties
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_sign_properties(arr):
    signs = np.sign(arr)
    
    for i, val in np.ndenumerate(arr):
        if val > 0:
            assert signs[i] == 1
        elif val < 0:
            assert signs[i] == -1
        else:
            assert signs[i] == 0


# Test 20: Testing copysign properties
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
def test_copysign_properties(x, y):
    result = np.copysign(x, y)
    
    # Magnitude should be from x, sign from y
    assert abs(result) == abs(x) or np.isclose(abs(result), abs(x))
    if y >= 0:
        assert result >= 0
    else:
        assert result <= 0


# Test 21: Testing partition preserves elements
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 50),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)),
       st.integers(0, 49))
def test_partition_preserves_elements(arr, kth):
    if kth >= len(arr):
        kth = len(arr) - 1
    
    partitioned = np.partition(arr, kth)
    
    # Should have same elements (multiset equality)
    assert np.array_equal(np.sort(partitioned), np.sort(arr))
    
    # kth element should be in correct position
    kth_element = partitioned[kth]
    # All elements before kth should be <= kth_element
    assert all(x <= kth_element or np.isclose(x, kth_element) for x in partitioned[:kth])
    # All elements after kth should be >= kth_element  
    assert all(x >= kth_element or np.isclose(x, kth_element) for x in partitioned[kth+1:])


# Test 22: Testing diagonal extraction and creation
@given(npst.arrays(dtype=np.float64, shape=(st.integers(2, 10), st.integers(2, 10)),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_diagonal_diag_consistency(matrix):
    # Make it square
    n = min(matrix.shape)
    matrix = matrix[:n, :n]
    
    # Extract diagonal
    diag = np.diagonal(matrix)
    
    # Create diagonal matrix
    diag_matrix = np.diag(diag)
    
    # Diagonal of diagonal matrix should be same
    assert np.array_equal(np.diagonal(diag_matrix), diag)


# Test 23: Testing ceil and floor relationship
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)))
def test_ceil_floor_relationship(arr):
    ceiled = np.ceil(arr)
    floored = np.floor(arr)
    
    # ceil >= original >= floor
    assert np.all(ceiled >= arr) or np.allclose(ceiled, arr)
    assert np.all(floored <= arr) or np.allclose(floored, arr)
    
    # For integers, ceil = floor = original
    int_mask = arr == np.round(arr)
    assert np.allclose(ceiled[int_mask], floored[int_mask])


# Test 24: Testing modf consistency
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_modf_consistency(arr):
    fractional, integral = np.modf(arr)
    
    # Sum should give original
    reconstructed = fractional + integral
    assert np.allclose(reconstructed, arr, rtol=1e-10)
    
    # Integral part should have no fractional component
    assert np.allclose(integral, np.trunc(integral))


# Test 25: Testing hypot properties
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5))
def test_hypot_properties(x, y):
    # hypot should compute sqrt(x^2 + y^2) accurately
    result = np.hypot(x, y)
    expected = np.sqrt(x*x + y*y)
    
    assert np.isclose(result, expected, rtol=1e-10)
    
    # Should be non-negative
    assert result >= 0
    
    # Should be >= max(|x|, |y|)
    assert result >= max(abs(x), abs(y)) or np.isclose(result, max(abs(x), abs(y)))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])