import numpy as np
import numpy.matlib as matlib
from hypothesis import given, strategies as st, assume, settings, example
import pytest
import sys


@given(st.integers())
def test_identity_with_invalid_types(n):
    """Test identity() with various integer values including edge cases"""
    if n < 0:
        # Negative dimensions should fail
        with pytest.raises((ValueError, TypeError)):
            matlib.identity(n)
    elif n == 0:
        # Zero dimension should work
        result = matlib.identity(0)
        assert result.shape == (0, 0)
        assert result.size == 0
    else:
        # Positive dimensions
        if n > sys.maxsize // (n + 1):
            # Very large n might cause overflow
            with pytest.raises((MemoryError, ValueError, OverflowError)):
                matlib.identity(n)
        elif n < 10000:  # Only test reasonable sizes
            result = matlib.identity(n)
            assert result.shape == (n, n)
            assert np.sum(result) == n


@given(st.integers(min_value=1, max_value=100))
def test_identity_flat_assignment_precision(n):
    """Test the flat assignment trick in identity() for correctness"""
    # The implementation does: 
    # a = array([1] + n * [0])
    # b.flat = a
    # This creates the identity by cycling through the pattern
    
    result = matlib.identity(n)
    
    # Manually verify each element
    for i in range(n):
        for j in range(n):
            if i == j:
                assert result[i, j] == 1, f"Diagonal element [{i},{j}] is not 1"
            else:
                assert result[i, j] == 0, f"Off-diagonal element [{i},{j}] is not 0"


@given(st.integers(min_value=-10, max_value=10),
       st.integers(min_value=-10, max_value=10))
def test_repmat_negative_or_zero(m, n):
    """Test repmat with negative and zero repetition counts"""
    arr = np.array([1, 2, 3])
    
    if m < 0 or n < 0:
        # Negative repetitions - what happens?
        try:
            result = matlib.repmat(arr, m, n)
            # If it works, it's treating negative as something
            print(f"Negative reps m={m}, n={n} gave shape: {result.shape}")
            
            # Check if negative is treated as 0
            if m < 0:
                expected_m = 0
            else:
                expected_m = m
            if n < 0:
                expected_n = 0
            else:
                expected_n = n
                
            # The shape calculation uses origrows * m and origcols * n
            # If negative values create negative dimensions, reshape will fail
            
        except (ValueError, TypeError) as e:
            # This is expected for negative values
            pass
    else:
        result = matlib.repmat(arr, m, n)
        assert result.shape == (m, n * 3)


@given(st.lists(st.integers(min_value=-100, max_value=100), 
                min_size=0, max_size=10),
       st.integers(min_value=1, max_value=5),
       st.integers(min_value=1, max_value=5))
def test_repmat_empty_array(arr, m, n):
    """Test repmat with empty arrays"""
    a = np.array(arr)
    
    if len(arr) == 0:
        # Empty array
        result = matlib.repmat(a, m, n)
        # Should create empty result
        assert result.size == 0
    else:
        result = matlib.repmat(a, m, n)
        # Check dimensions
        if a.ndim == 1:
            assert result.shape == (m, n * len(arr))


@given(st.integers(min_value=1, max_value=50))
def test_eye_with_none_M(n):
    """Test eye() with M=None (should default to n)"""
    result = matlib.eye(n, M=None)
    expected = matlib.identity(n)
    assert np.array_equal(result, expected)


@given(st.integers(min_value=1, max_value=20),
       st.integers(min_value=1, max_value=20))
def test_matrix_type_preservation(m, n):
    """Ensure all functions return matrix type, not ndarray"""
    # Test all matrix creation functions
    ones_mat = matlib.ones((m, n))
    zeros_mat = matlib.zeros((m, n))
    empty_mat = matlib.empty((m, n))
    
    assert isinstance(ones_mat, np.matrix)
    assert isinstance(zeros_mat, np.matrix)
    assert isinstance(empty_mat, np.matrix)
    
    if m == n:
        identity_mat = matlib.identity(m)
        assert isinstance(identity_mat, np.matrix)
    
    eye_mat = matlib.eye(m, M=n)
    assert isinstance(eye_mat, np.matrix)
    
    rand_mat = matlib.rand(m, n)
    randn_mat = matlib.randn(m, n)
    assert isinstance(rand_mat, np.matrix)
    assert isinstance(randn_mat, np.matrix)


@given(st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10),
       st.integers(min_value=1, max_value=10))
def test_repmat_dimension_calculation(r, c, m, n):
    """Test repmat's dimension calculations in detail"""
    # Create test array
    arr = np.arange(r * c).reshape(r, c)
    
    result = matlib.repmat(arr, m, n)
    
    # According to the implementation:
    # rows = origrows * m
    # cols = origcols * n
    assert result.shape[0] == r * m
    assert result.shape[1] == c * n
    
    # Verify the tiling pattern
    for i in range(m):
        for j in range(n):
            tile = result[i*r:(i+1)*r, j*c:(j+1)*c]
            assert np.array_equal(tile, arr)


@given(st.integers(min_value=0, max_value=5),
       st.integers(min_value=0, max_value=5))
def test_ones_zeros_with_zero_dim(m, n):
    """Test ones/zeros with dimensions including 0"""
    # Create with potentially zero dimensions
    ones_mat = matlib.ones((m, n))
    zeros_mat = matlib.zeros((m, n))
    
    assert ones_mat.shape == (m, n)
    assert zeros_mat.shape == (m, n)
    
    if m == 0 or n == 0:
        assert ones_mat.size == 0
        assert zeros_mat.size == 0
    else:
        assert np.all(ones_mat == 1)
        assert np.all(zeros_mat == 0)


@given(st.floats(min_value=0.0, max_value=100.0))
def test_functions_with_float_dimensions(x):
    """Test matrix functions with float dimensions"""
    # These should only accept integers
    
    if x == int(x):
        # If it's actually an integer value, it might work
        n = int(x)
        if n > 0:
            result = matlib.ones(x)  # Pass float
            assert result.shape == (1, n)
    else:
        # Non-integer floats should fail
        with pytest.raises((TypeError, ValueError)):
            matlib.ones(x)


@given(st.integers(min_value=1, max_value=100))
def test_identity_diagonal_uniqueness(n):
    """Verify identity matrix has exactly n ones and n²-n zeros"""
    result = matlib.identity(n)
    
    # Count 1s and 0s
    ones_count = np.sum(result == 1)
    zeros_count = np.sum(result == 0)
    
    assert ones_count == n  # Exactly n ones (on diagonal)
    assert zeros_count == n * n - n  # Rest are zeros
    assert ones_count + zeros_count == n * n  # Total elements


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"] + sys.argv[1:])