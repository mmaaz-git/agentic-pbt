import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.extra import numpy as npst
import math


# Strategy for valid floating point arrays
valid_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
small_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)
positive_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=1e-10, max_value=1e10)


# Test 1: sqrt/square round-trip property
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2), 
                   elements=positive_floats))
def test_sqrt_square_roundtrip(arr):
    sqrt_arr = np.sqrt(arr)
    squared = np.square(sqrt_arr)
    assert np.allclose(squared, arr, rtol=1e-10)


# Test 2: square/sqrt round-trip for positive values
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(min_value=0.0, max_value=1e5, allow_nan=False)))
def test_square_sqrt_roundtrip(arr):
    squared = np.square(arr)
    sqrt_result = np.sqrt(squared)
    assert np.allclose(sqrt_result, arr, rtol=1e-10)


# Test 3: sort invariant - sorted array contains same elements
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=valid_floats))
def test_sort_preserves_elements(arr):
    sorted_arr = np.sort(arr)
    assert len(sorted_arr) == len(arr)
    # Check multiset equality
    assert np.allclose(np.sort(arr), np.sort(sorted_arr))


# Test 4: unique invariant - unique elements are subset of original
@given(npst.arrays(dtype=np.int32, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=st.integers(-1000, 1000)))
def test_unique_subset(arr):
    unique_arr = np.unique(arr)
    assert len(unique_arr) <= len(arr)
    # All unique elements should be in original
    for elem in unique_arr:
        assert elem in arr


# Test 5: concatenate/split inverse property
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=2, max_side=100),
                   elements=valid_floats))
def test_concatenate_split_inverse(arr):
    # Split into 2 parts
    mid = len(arr) // 2
    assume(mid > 0)
    splits = np.split(arr, [mid])
    reconstructed = np.concatenate(splits)
    assert np.array_equal(reconstructed, arr)


# Test 6: matrix inverse property for well-conditioned matrices - FIXED
@given(n=st.integers(2, 10))
def test_matrix_inverse_property(n):
    # Create a well-conditioned matrix
    np.random.seed(42)
    # Create orthogonal matrix Q via QR decomposition
    A = np.random.randn(n, n)
    Q, _ = np.linalg.qr(A)
    # Create diagonal matrix with reasonable eigenvalues
    D = np.diag(np.random.uniform(0.1, 10, n))
    # Create well-conditioned matrix
    matrix = Q @ D @ Q.T
    
    inv_matrix = np.linalg.inv(matrix)
    product = np.matmul(matrix, inv_matrix)
    identity = np.eye(n)
    
    assert np.allclose(product, identity, rtol=1e-10, atol=1e-12)


# Test 7: solve/matmul consistency - FIXED
@given(n=st.integers(2, 10))
def test_solve_matmul_consistency(n):
    # Create well-conditioned system
    np.random.seed(42)
    A = np.random.randn(n, n)
    Q, _ = np.linalg.qr(A)
    D = np.diag(np.random.uniform(0.1, 10, n))
    A = Q @ D @ Q.T
    
    b = np.random.randn(n)
    
    # Solve Ax = b
    x = np.linalg.solve(A, b)
    
    # Verify A @ x = b
    result = np.matmul(A, x)
    assert np.allclose(result, b, rtol=1e-10, atol=1e-12)


# Test 8: Metamorphic property for sin
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_sin_metamorphic(x):
    # sin(π - x) = sin(x)
    left = np.sin(np.pi - x)
    right = np.sin(x)
    assert np.isclose(left, right, rtol=1e-10)


# Test 9: cos metamorphic property
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_cos_metamorphic(x):
    # cos(-x) = cos(x)
    assert np.isclose(np.cos(-x), np.cos(x), rtol=1e-10)


# Test 10: argmax/argmin consistency
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=valid_floats))
def test_argmax_argmin_consistency(arr):
    if len(arr) > 0:
        max_idx = np.argmax(arr)
        min_idx = np.argmin(arr)
        
        # The element at argmax should be >= all elements
        # The element at argmin should be <= all elements
        max_val = arr[max_idx]
        min_val = arr[min_idx]
        
        for val in arr:
            assert val <= max_val or np.isclose(val, max_val)
            assert val >= min_val or np.isclose(val, min_val)


# Test 11: clip invariant
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=valid_floats),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5))
def test_clip_invariant(arr, a_min, a_max):
    if a_min > a_max:
        a_min, a_max = a_max, a_min
    
    clipped = np.clip(arr, a_min, a_max)
    
    # All values should be within bounds
    assert np.all(clipped >= a_min)
    assert np.all(clipped <= a_max)
    
    # Values within bounds should be unchanged
    mask = (arr >= a_min) & (arr <= a_max)
    assert np.allclose(arr[mask], clipped[mask])


# Test 12: mean property
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=small_floats))
def test_mean_property(arr):
    mean = np.mean(arr)
    # Mean should be between min and max
    assert np.min(arr) <= mean <= np.max(arr) or np.isclose(mean, np.min(arr)) or np.isclose(mean, np.max(arr))


# Test 13: dot product commutativity for 1D arrays  
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=small_floats),
       npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=small_floats))
def test_dot_commutativity_1d(a, b):
    # Make same size
    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]
    
    result1 = np.dot(a, b)
    result2 = np.dot(b, a)
    assert np.isclose(result1, result2, rtol=1e-10)


# Test 14: exp/log inverse
@given(st.floats(min_value=1e-10, max_value=100, allow_nan=False))
def test_exp_log_inverse(x):
    log_x = np.log(x)
    exp_log_x = np.exp(log_x)
    assert np.isclose(exp_log_x, x, rtol=1e-10)


# Test 15: log/exp inverse
@given(st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_log_exp_inverse(x):
    exp_x = np.exp(x)
    log_exp_x = np.log(exp_x)
    assert np.isclose(log_exp_x, x, rtol=1e-10)


# Test 16: abs idempotence
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=valid_floats))
def test_abs_idempotence(arr):
    abs1 = np.abs(arr)
    abs2 = np.abs(abs1)
    assert np.allclose(abs1, abs2)


# Test 17: add/subtract inverse - FIXED to handle broadcasting properly
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=small_floats))
def test_add_subtract_inverse(arr):
    # Test with scalar
    scalar = 5.0
    added = np.add(arr, scalar)
    subtracted = np.subtract(added, scalar)
    assert np.allclose(subtracted, arr, rtol=1e-10)


# Test 18: power properties
@given(st.floats(min_value=0.1, max_value=10, allow_nan=False),
       st.integers(1, 10),
       st.integers(1, 10))
def test_power_properties(base, exp1, exp2):
    # (a^m)^n = a^(m*n)
    result1 = np.power(np.power(base, exp1), exp2)
    result2 = np.power(base, exp1 * exp2)
    assert np.isclose(result1, result2, rtol=1e-10)


# Test 19: where function consistency
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=valid_floats))
def test_where_consistency(arr):
    condition = arr > 0
    result = np.where(condition, arr, 0)
    
    # Check that positive values are preserved and negative are zeroed
    for i, val in enumerate(arr):
        if val > 0:
            assert result[i] == val
        else:
            assert result[i] == 0


# Test 20: reshape invariant
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=3, min_side=1),
                   elements=valid_floats))
def test_reshape_preserves_elements(arr):
    flat = arr.flatten()
    # Reshape to different valid shape
    new_shape = (-1, 1) if len(flat) > 0 else (0,)
    reshaped = np.reshape(arr, new_shape)
    flat_reshaped = reshaped.flatten()
    
    assert np.array_equal(flat, flat_reshaped)


# Additional tests for edge cases and potential bugs

# Test 21: Testing array conversion with special values
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_array_conversion_preserves_values(lst):
    arr = np.array(lst)
    for i, val in enumerate(lst):
        assert arr[i] == val or np.isclose(arr[i], val)


# Test 22: Testing histogram edge cases
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_histogram_sum(arr):
    if len(arr) > 0:
        hist, bins = np.histogram(arr, bins=10)
        # Total count should equal array length
        assert np.sum(hist) == len(arr)


# Test 23: Testing cumsum property
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=1, min_side=1),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_cumsum_last_element(arr):
    cumsum = np.cumsum(arr)
    # Last element of cumsum should equal sum of array
    assert np.isclose(cumsum[-1], np.sum(arr), rtol=1e-10)


# Test 24: Testing diff inverse
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_diff_cumsum_inverse(arr):
    # diff and cumsum are almost inverse
    diff_arr = np.diff(arr)
    # Reconstruct by adding first element and cumsum of diff
    reconstructed = np.concatenate([[arr[0]], arr[0] + np.cumsum(diff_arr)])
    assert np.allclose(reconstructed, arr, rtol=1e-10)


# Test 25: Testing median property
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_median_property(arr):
    median = np.median(arr)
    # Median should be between min and max
    assert np.min(arr) <= median <= np.max(arr) or np.isclose(median, np.min(arr)) or np.isclose(median, np.max(arr))


# Test 26: Testing percentile consistency
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_percentile_consistency(arr):
    p0 = np.percentile(arr, 0)
    p100 = np.percentile(arr, 100)
    p50 = np.percentile(arr, 50)
    
    # 0th percentile should be min, 100th should be max
    assert np.isclose(p0, np.min(arr), rtol=1e-10)
    assert np.isclose(p100, np.max(arr), rtol=1e-10)
    # 50th percentile should be median
    assert np.isclose(p50, np.median(arr), rtol=1e-10)


# Test 27: Testing std is non-negative
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_std_non_negative(arr):
    std = np.std(arr)
    assert std >= 0 or np.isclose(std, 0)


# Test 28: Testing var is non-negative
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_var_non_negative(arr):
    var = np.var(arr)
    assert var >= 0 or np.isclose(var, 0)


# Test 29: Testing var = std^2
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)))
def test_var_std_relationship(arr):
    var = np.var(arr)
    std = np.std(arr)
    assert np.isclose(var, std**2, rtol=1e-10)


# Test 30: Testing roll preserves elements
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5)),
       st.integers(-200, 200))
def test_roll_preserves_elements(arr, shift):
    rolled = np.roll(arr, shift)
    # Sorting should give same result
    assert np.array_equal(np.sort(arr), np.sort(rolled))


if __name__ == "__main__":
    # Run with increased examples for better coverage
    pytest.main([__file__, "-v", "--tb=short"])