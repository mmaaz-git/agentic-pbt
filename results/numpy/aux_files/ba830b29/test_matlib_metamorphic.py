import numpy as np
import numpy.matlib as matlib
from hypothesis import given, strategies as st, assume, settings
import pytest
import warnings


@given(st.integers(min_value=1, max_value=20),
       st.integers(min_value=1, max_value=20))
def test_repmat_reshape_consistency(m, n):
    """Test that repmat behaves consistently with reshape operations"""
    # Create a simple array
    arr = np.array([1, 2, 3, 4])
    
    # Test 1D array behavior
    result = matlib.repmat(arr, m, n)
    
    # According to the code, 1D arrays should be treated as (1, len) shape
    # So repmat should create (m, n*len(arr)) result
    assert result.shape == (m, n * 4)
    
    # Verify the pattern
    for i in range(m):
        for j in range(n):
            segment = result[i, j*4:(j+1)*4] 
            assert np.array_equal(segment, arr)


@given(st.integers(min_value=1, max_value=20))
def test_repmat_scalar_vs_array(n):
    """Test repmat with scalar (0-D array) input"""
    scalar = np.array(42)  # 0-D array
    result = matlib.repmat(scalar, n, n)
    
    # According to code, 0-D arrays are treated as (1,1) shape
    # So result should be (n, n)
    assert result.shape == (n, n)
    assert np.all(result == 42)


@given(st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10))
def test_repmat_with_matrix_input(r, c, m, n):
    """Test repmat specifically with matrix (not array) input"""
    # Create a matrix using matlib
    mat = matlib.ones((r, c))
    mat.fill(7)  # Fill with a specific value
    
    result = matlib.repmat(mat, m, n)
    
    assert result.shape == (r * m, c * n)
    assert np.all(result == 7)
    
    # Verify it returns the same type
    assert type(result) == type(mat)


@given(st.integers(min_value=1, max_value=100))
def test_identity_implementation_detail(n):
    """Test the specific flat assignment implementation of identity()"""
    # The implementation creates [1, 0, 0, ..., 0] of length n+1
    # Then assigns it cyclically to an n×n matrix using flat assignment
    
    # This works because diagonal positions are at indices 0, n+1, 2(n+1), ...
    # in the flattened array, and these all map to index 0 of the pattern
    
    # Let's verify this produces the correct result even for edge cases
    result = matlib.identity(n)
    
    # Create expected identity matrix
    expected = np.zeros((n, n))
    np.fill_diagonal(expected, 1)
    
    assert np.array_equal(result, expected)
    
    # Additional check: sum should equal n (only diagonal elements are 1)
    assert np.sum(result) == n


@given(st.integers(min_value=0, max_value=100),
       st.integers(min_value=0, max_value=100))
def test_repmat_with_zeros(m, n):
    """Test repmat edge case with zero repetitions"""
    arr = np.array([1, 2, 3])
    
    if m == 0 or n == 0:
        result = matlib.repmat(arr, m, n)
        # Should create empty array with appropriate dimensions
        assert result.shape == (m, n * 3)
        assert result.size == 0
    else:
        result = matlib.repmat(arr, m, n)
        assert result.shape == (m, n * 3)
        # Check first row
        for j in range(n):
            assert np.array_equal(result[0, j*3:(j+1)*3], arr)


@given(st.integers(min_value=1, max_value=50),
       st.integers(min_value=1, max_value=50),
       st.integers(min_value=-100, max_value=100))
def test_eye_diagonal_count(n, m, k):
    """Test that eye() has correct number of 1s on diagonal"""
    result = matlib.eye(n, M=m, k=k)
    
    # Count the number of 1s
    ones_count = np.sum(result == 1)
    
    # Calculate expected number of diagonal elements
    if k >= 0:
        # Upper diagonal
        if k >= m:
            expected = 0
        else:
            expected = min(n, m - k)
    else:
        # Lower diagonal
        if -k >= n:
            expected = 0
        else:
            expected = min(n + k, m)
    
    assert ones_count == expected
    
    # All non-diagonal elements should be 0
    assert np.sum(np.abs(result)) == ones_count


@given(st.integers(min_value=1, max_value=20),
       st.integers(min_value=1, max_value=20))
def test_ones_zeros_complementary(m, n):
    """Test that ones and zeros are complementary"""
    ones_mat = matlib.ones((m, n))
    zeros_mat = matlib.zeros((m, n))
    
    # Their sum should be all ones
    sum_mat = ones_mat + zeros_mat
    assert np.all(sum_mat == 1)
    
    # Their difference should be all ones
    diff_mat = ones_mat - zeros_mat
    assert np.all(diff_mat == 1)
    
    # Product should be all zeros
    prod_mat = ones_mat * zeros_mat
    assert np.all(prod_mat == 0)


@given(st.integers(min_value=1, max_value=20))
def test_identity_multiplication_property(n):
    """Test that identity matrix behaves as multiplicative identity"""
    I = matlib.identity(n)
    
    # Create a test matrix
    A = matlib.rand(n, n)
    
    # I * A should equal A
    result1 = I @ A
    assert np.allclose(result1, A)
    
    # A * I should equal A  
    result2 = A @ I
    assert np.allclose(result2, A)
    
    # I * I should equal I
    result3 = I @ I
    assert np.allclose(result3, I)


@given(st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10))
def test_repmat_size_calculation(r, c, m, n):
    """Test that repmat calculates sizes correctly"""
    # Create array with known size
    arr = np.ones((r, c))
    result = matlib.repmat(arr, m, n)
    
    # Check dimensions
    assert result.shape == (r * m, c * n)
    assert result.size == r * c * m * n
    
    # Check that the tiling is correct
    for i in range(m):
        for j in range(n):
            tile = result[i*r:(i+1)*r, j*c:(j+1)*c]
            assert tile.shape == (r, c)
            assert np.array_equal(tile, arr)


@given(st.integers(min_value=1, max_value=100))
def test_single_arg_to_matrix_functions(n):
    """Test single integer argument behavior for matrix creation functions"""
    # According to docs, single dimension should create (1, n) matrix
    
    ones_result = matlib.ones(n)
    assert ones_result.shape == (1, n)
    
    zeros_result = matlib.zeros(n) 
    assert zeros_result.shape == (1, n)
    
    empty_result = matlib.empty(n)
    assert empty_result.shape == (1, n)
    
    # All should be matrix type
    assert isinstance(ones_result, np.matrix)
    assert isinstance(zeros_result, np.matrix)
    assert isinstance(empty_result, np.matrix)


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "--tb=short"] + sys.argv[1:])