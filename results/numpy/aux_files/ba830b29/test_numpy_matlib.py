import numpy as np
import numpy.matlib as matlib
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


# Strategy for valid matrix dimensions
dims = st.integers(min_value=1, max_value=100)
small_dims = st.integers(min_value=1, max_value=20)


@given(dims)
def test_ones_single_dimension_becomes_row_matrix(n):
    """Single dimension input to ones() should create (1, n) matrix"""
    result = matlib.ones(n)
    assert result.shape == (1, n)
    assert result.ndim == 2
    assert np.all(result == 1)


@given(dims)
def test_zeros_single_dimension_becomes_row_matrix(n):
    """Single dimension input to zeros() should create (1, n) matrix"""
    result = matlib.zeros(n)
    assert result.shape == (1, n)
    assert result.ndim == 2
    assert np.all(result == 0)


@given(dims, dims)
def test_ones_fills_correctly(m, n):
    """ones() should fill matrix with 1s"""
    result = matlib.ones((m, n))
    assert result.shape == (m, n)
    assert np.all(result == 1)
    assert result.sum() == m * n


@given(dims, dims)
def test_zeros_fills_correctly(m, n):
    """zeros() should fill matrix with 0s"""
    result = matlib.zeros((m, n))
    assert result.shape == (m, n)
    assert np.all(result == 0)
    assert result.sum() == 0


@given(dims)
def test_identity_is_square(n):
    """identity() should create square matrix"""
    result = matlib.identity(n)
    assert result.shape == (n, n)
    assert result.ndim == 2


@given(dims)
def test_identity_diagonal_property(n):
    """identity() should have 1s on diagonal, 0s elsewhere"""
    result = matlib.identity(n)
    # Check diagonal
    assert np.all(np.diag(result) == 1)
    # Check sum equals n (only diagonal elements are 1)
    assert result.sum() == n
    # Check off-diagonal elements
    for i in range(n):
        for j in range(n):
            if i == j:
                assert result[i, j] == 1
            else:
                assert result[i, j] == 0


@given(dims, st.integers(min_value=0, max_value=100))
def test_eye_diagonal_offset(n, k):
    """eye() should correctly place 1s on k-th diagonal"""
    assume(k < n)  # Only test reasonable offsets
    result = matlib.eye(n, k=k)
    
    # Count 1s - should equal number of diagonal elements
    ones_count = np.sum(result == 1)
    expected_count = max(0, n - abs(k))
    assert ones_count == expected_count
    
    # Check all other elements are 0
    assert np.sum(result) == ones_count


@given(dims, dims, st.integers(min_value=-20, max_value=20))
def test_eye_rectangular_with_offset(n, m, k):
    """eye() should handle rectangular matrices with offset"""
    result = matlib.eye(n, M=m, k=k)
    assert result.shape == (n, m)
    
    # Calculate expected number of 1s on diagonal
    if k >= 0:
        # Upper diagonal
        expected_ones = max(0, min(n, m - k))
    else:
        # Lower diagonal
        expected_ones = max(0, min(n + k, m))
    
    assert np.sum(result == 1) == expected_ones


@given(st.integers(min_value=0, max_value=10), small_dims, small_dims)
def test_repmat_scalar(val, m, n):
    """repmat() should correctly repeat scalar values"""
    a = np.array(val)
    result = matlib.repmat(a, m, n)
    assert result.shape == (m, n)
    assert np.all(result == val)


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10), 
       small_dims, small_dims)
def test_repmat_1d_array(arr, m, n):
    """repmat() should correctly repeat 1D arrays"""
    a = np.array(arr)
    result = matlib.repmat(a, m, n)
    
    expected_shape = (m, n * len(arr))
    assert result.shape == expected_shape
    
    # Check that pattern is repeated correctly
    for i in range(m):
        for j in range(n):
            segment = result[i, j*len(arr):(j+1)*len(arr)]
            assert np.array_equal(segment, arr)


@given(small_dims, small_dims, small_dims, small_dims)
def test_repmat_2d_preserves_values(r, c, m, n):
    """repmat() should preserve all original values when repeating 2D array"""
    # Create test matrix with unique values
    original = np.arange(r * c).reshape(r, c)
    original_matrix = np.asmatrix(original)
    
    result = matlib.repmat(original_matrix, m, n)
    
    assert result.shape == (r * m, c * n)
    
    # Check each tile
    for i in range(m):
        for j in range(n):
            tile = result[i*r:(i+1)*r, j*c:(j+1)*c]
            assert np.array_equal(tile, original)


@given(dims)
def test_empty_returns_matrix_type(n):
    """empty() should return matrix type"""
    result = matlib.empty((n, n))
    assert isinstance(result, np.matrix)
    assert result.shape == (n, n)


@given(dims)
def test_identity_inverse_property(n):
    """Identity matrix should be its own inverse"""
    I = matlib.identity(n)
    product = I @ I
    assert np.allclose(product, I)
    assert np.allclose(np.linalg.det(I), 1.0)


@given(st.tuples(dims, dims))
def test_rand_shape_tuple_vs_args(shape):
    """rand() should handle tuple and separate args identically"""
    np.random.seed(42)
    r1 = matlib.rand(shape)
    
    np.random.seed(42)
    r2 = matlib.rand(*shape)
    
    assert r1.shape == r2.shape
    assert np.array_equal(r1, r2)


@given(st.tuples(dims, dims))
def test_randn_shape_tuple_vs_args(shape):
    """randn() should handle tuple and separate args identically"""
    np.random.seed(42)
    r1 = matlib.randn(shape)
    
    np.random.seed(42)
    r2 = matlib.randn(*shape)
    
    assert r1.shape == r2.shape
    assert np.array_equal(r1, r2)


@given(dims)
def test_identity_implementation_bug(n):
    """Test the specific implementation of identity()"""
    # The identity function uses a clever but potentially buggy implementation
    result = matlib.identity(n)
    
    # Verify it's actually an identity matrix
    expected = np.eye(n)
    assert np.array_equal(result, expected)
    
    # Check that modifying one element doesn't affect others
    result_copy = result.copy()
    if n > 1:
        result_copy[0, 1] = 999
        assert result_copy[1, 0] != 999  # Should not be affected


@given(small_dims, small_dims)
def test_repmat_empty_handling(m, n):
    """Test repmat with edge cases"""
    # Empty array
    empty = np.array([])
    result = matlib.repmat(empty, m, n)
    assert result.size == 0
    
    # 0-d array edge case
    scalar = np.array(5)
    result = matlib.repmat(scalar, m, n)
    assert result.shape == (m, n)
    assert np.all(result == 5)


@given(dims, dims)
def test_eye_default_diagonal(n, m):
    """eye() with k=0 should match identity for square matrices"""
    result = matlib.eye(n, M=m, k=0)
    
    if n == m:
        # For square matrices, should match identity
        identity = matlib.identity(n)
        assert np.array_equal(result, identity)
    
    # Check diagonal
    min_dim = min(n, m)
    for i in range(min_dim):
        assert result[i, i] == 1


if __name__ == "__main__":
    # Run all tests
    import sys
    pytest.main([__file__, "-v", "--tb=short"] + sys.argv[1:])