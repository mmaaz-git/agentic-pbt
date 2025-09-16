import numpy as np
import scipy.sparse as sp
from hypothesis import given, strategies as st, settings, assume
import pytest


@given(
    data=st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=1, max_size=100),
    rows=st.lists(st.integers(min_value=0, max_value=99), min_size=1, max_size=100),
    cols=st.lists(st.integers(min_value=0, max_value=99), min_size=1, max_size=100),
)
@settings(max_examples=100)
def test_format_conversion_round_trip(data, rows, cols):
    """Test that converting between sparse formats preserves data."""
    # Ensure consistent lengths
    min_len = min(len(data), len(rows), len(cols))
    data = data[:min_len]
    rows = rows[:min_len]
    cols = cols[:min_len]
    
    assume(len(data) > 0)
    
    # Create a COO matrix
    shape = (max(rows) + 1, max(cols) + 1) if rows and cols else (1, 1)
    coo = sp.coo_matrix((data, (rows, cols)), shape=shape)
    
    # Convert to different formats and back
    csr = coo.tocsr()
    csc = coo.tocsc()
    dok = coo.todok()
    
    # Convert back to COO
    coo_from_csr = csr.tocoo()
    coo_from_csc = csc.tocoo()
    coo_from_dok = dok.tocoo()
    
    # Check that data is preserved
    assert np.allclose(coo.toarray(), coo_from_csr.toarray())
    assert np.allclose(coo.toarray(), coo_from_csc.toarray())
    assert np.allclose(coo.toarray(), coo_from_dok.toarray())


@given(
    m1_rows=st.integers(min_value=1, max_value=10),
    m1_cols=st.integers(min_value=1, max_value=10),
    m2_cols=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_hstack_dimensions(m1_rows, m1_cols, m2_cols):
    """Test that hstack produces correct dimensions."""
    # Create two sparse matrices with compatible shapes for hstack
    m1 = sp.random(m1_rows, m1_cols, density=0.5, format='csr')
    m2 = sp.random(m1_rows, m2_cols, density=0.5, format='csr')
    
    # Stack horizontally
    result = sp.hstack([m1, m2])
    
    # Check dimensions
    assert result.shape == (m1_rows, m1_cols + m2_cols)
    
    # Check that values are preserved
    expected = np.hstack([m1.toarray(), m2.toarray()])
    assert np.allclose(result.toarray(), expected)


@given(
    m1_rows=st.integers(min_value=1, max_value=10),
    m1_cols=st.integers(min_value=1, max_value=10),
    m2_rows=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_vstack_dimensions(m1_rows, m1_cols, m2_rows):
    """Test that vstack produces correct dimensions."""
    # Create two sparse matrices with compatible shapes for vstack
    m1 = sp.random(m1_rows, m1_cols, density=0.5, format='csr')
    m2 = sp.random(m2_rows, m1_cols, density=0.5, format='csr')
    
    # Stack vertically
    result = sp.vstack([m1, m2])
    
    # Check dimensions
    assert result.shape == (m1_rows + m2_rows, m1_cols)
    
    # Check that values are preserved
    expected = np.vstack([m1.toarray(), m2.toarray()])
    assert np.allclose(result.toarray(), expected)


@given(
    n=st.integers(min_value=1, max_value=20),
    k=st.integers(min_value=-19, max_value=19),
)
@settings(max_examples=100)
def test_eye_identity_property(n, k):
    """Test that eye creates correct identity-like matrices."""
    # Create sparse eye matrix
    eye_matrix = sp.eye(n, k=k)
    dense = eye_matrix.toarray()
    
    # Check shape
    assert dense.shape == (n, n)
    
    # Check diagonal values
    if abs(k) < n:
        # Get the diagonal at offset k
        diagonal = np.diag(dense, k=k)
        if k >= 0:
            expected_length = min(n, n - k)
        else:
            expected_length = min(n, n + k)
        
        assert len(diagonal) == expected_length
        assert np.all(diagonal == 1.0)
    
    # Check non-diagonal values are zero
    for i in range(n):
        for j in range(n):
            if j - i == k and 0 <= i < n and 0 <= j < n:
                assert dense[i, j] == 1.0
            else:
                assert dense[i, j] == 0.0


@given(
    diag_values=st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=1, max_size=10),
    offset=st.integers(min_value=-5, max_value=5),
    size=st.integers(min_value=1, max_value=15),
)
@settings(max_examples=100) 
def test_diags_diagonal_placement(diag_values, offset, size):
    """Test that diags places values on correct diagonals."""
    # Adjust size to accommodate the diagonal
    min_size = abs(offset) + len(diag_values)
    size = max(size, min_size)
    
    # Create diagonal matrix
    diag_matrix = sp.diags(diag_values, offset, shape=(size, size))
    dense = diag_matrix.toarray()
    
    # Check that values are on the correct diagonal
    extracted_diagonal = np.diag(dense, k=offset)
    
    # The extracted diagonal should match our input (up to the size limit)
    expected_length = min(len(diag_values), len(extracted_diagonal))
    assert np.allclose(extracted_diagonal[:expected_length], diag_values[:expected_length])


@given(
    rows=st.integers(min_value=1, max_value=20),
    cols=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=100)
def test_transpose_involution(rows, cols):
    """Test that transpose is an involution: (A.T).T = A"""
    # Create a random sparse matrix
    matrix = sp.random(rows, cols, density=0.5, format='csr')
    
    # Transpose twice
    transposed = matrix.transpose()
    double_transposed = transposed.transpose()
    
    # Should get back the original
    assert np.allclose(matrix.toarray(), double_transposed.toarray())
    assert matrix.shape == double_transposed.shape


@given(
    size=st.integers(min_value=1, max_value=15),
)
@settings(max_examples=100)
def test_identity_multiplication(size):
    """Test that I * A = A for identity matrix I"""
    # Create identity matrix
    identity = sp.eye(size)
    
    # Create a random matrix
    matrix = sp.random(size, size, density=0.5, format='csr')
    
    # Multiply by identity
    result = identity @ matrix
    
    # Should get back the original
    assert np.allclose(matrix.toarray(), result.toarray())


@given(
    rows=st.integers(min_value=1, max_value=15),
    cols=st.integers(min_value=1, max_value=15),
    scalar=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
)
@settings(max_examples=100)
def test_scalar_multiplication_commutativity(rows, cols, scalar):
    """Test that scalar multiplication is commutative: c*A = A*c"""
    # Create a random sparse matrix
    matrix = sp.random(rows, cols, density=0.5, format='csr')
    
    # Multiply by scalar from left and right
    left_mult = scalar * matrix
    right_mult = matrix * scalar
    
    # Should be the same
    assert np.allclose(left_mult.toarray(), right_mult.toarray())