import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings
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


# Test 6: matrix inverse property for well-conditioned matrices
@given(npst.arrays(dtype=np.float64, shape=(st.integers(2, 10), st.integers(2, 10)),
                   elements=small_floats))
def test_matrix_inverse_property(matrix):
    # Make it square
    n = min(matrix.shape)
    matrix = matrix[:n, :n]
    
    # Check if matrix is invertible (non-singular)
    try:
        det = np.linalg.det(matrix)
        assume(abs(det) > 1e-10)  # Skip singular matrices
        
        inv_matrix = np.linalg.inv(matrix)
        product = np.matmul(matrix, inv_matrix)
        identity = np.eye(n)
        
        assert np.allclose(product, identity, rtol=1e-5, atol=1e-8)
    except np.linalg.LinAlgError:
        # Skip singular matrices
        assume(False)


# Test 7: solve/matmul consistency
@given(npst.arrays(dtype=np.float64, shape=(st.integers(2, 10), st.integers(2, 10)),
                   elements=small_floats),
       npst.arrays(dtype=np.float64, shape=st.integers(2, 10),
                   elements=small_floats))
def test_solve_matmul_consistency(A, b):
    # Make A square
    n = min(A.shape[0], A.shape[1], len(b))
    A = A[:n, :n]
    b = b[:n]
    
    try:
        # Check matrix is non-singular
        det = np.linalg.det(A)
        assume(abs(det) > 1e-10)
        
        # Solve Ax = b
        x = np.linalg.solve(A, b)
        
        # Verify A @ x = b
        result = np.matmul(A, x)
        assert np.allclose(result, b, rtol=1e-5, atol=1e-8)
    except np.linalg.LinAlgError:
        assume(False)


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


# Test 17: add/subtract inverse
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=small_floats),
       npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=small_floats))
def test_add_subtract_inverse(a, b):
    # Make same shape
    if a.shape != b.shape:
        min_shape = tuple(min(s1, s2) for s1, s2 in zip(a.shape, b.shape))
        a = a[tuple(slice(s) for s in min_shape)]
        b = b[tuple(slice(s) for s in min_shape)]
    
    added = np.add(a, b)
    subtracted = np.subtract(added, b)
    assert np.allclose(subtracted, a, rtol=1e-10)


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


if __name__ == "__main__":
    # Run with increased examples for better coverage
    pytest.main([__file__, "-v", "--tb=short"])