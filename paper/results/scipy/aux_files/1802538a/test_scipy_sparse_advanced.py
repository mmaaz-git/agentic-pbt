import numpy as np
import scipy.sparse as sp
from hypothesis import given, strategies as st, settings, assume
import pytest
import math


@given(
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
    density=st.floats(min_value=0.1, max_value=0.9),
)
@settings(max_examples=100)
def test_transpose_nnz_invariant(rows, cols, density):
    """Test that transpose preserves number of non-zero elements."""
    matrix = sp.random(rows, cols, density=density, format='csr')
    transposed = matrix.transpose()
    
    # Number of non-zero elements should be preserved
    assert matrix.nnz == transposed.nnz


@given(
    size=st.integers(min_value=2, max_value=10),
    density=st.floats(min_value=0.1, max_value=0.9),
)
@settings(max_examples=100)
def test_diagonal_extraction_consistency(size, density):
    """Test that diagonal extraction is consistent across formats."""
    # Create a square matrix
    matrix = sp.random(size, size, density=density, format='csr')
    
    # Extract diagonal in different formats
    csr_diag = matrix.diagonal()
    csc_diag = matrix.tocsc().diagonal()
    coo_diag = matrix.tocoo().diagonal()
    
    # All should be the same
    assert np.allclose(csr_diag, csc_diag)
    assert np.allclose(csr_diag, coo_diag)


@given(
    rows=st.integers(min_value=1, max_value=10),
    inner=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
    density=st.floats(min_value=0.1, max_value=0.5),
)
@settings(max_examples=50)
def test_matrix_multiplication_format_consistency(rows, inner, cols, density):
    """Test that matrix multiplication gives same result across formats."""
    A = sp.random(rows, inner, density=density, format='csr', random_state=42)
    B = sp.random(inner, cols, density=density, format='csr', random_state=43)
    
    # Multiply in different formats
    result_csr = (A @ B).toarray()
    result_csc = (A.tocsc() @ B.tocsc()).toarray()
    result_coo = (A.tocoo() @ B.tocoo()).toarray()
    
    # Results should be the same
    assert np.allclose(result_csr, result_csc)
    assert np.allclose(result_csr, result_coo)


@given(
    size=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100)
def test_identity_is_identity(size):
    """Test that identity matrix behaves as mathematical identity."""
    I = sp.eye(size)
    
    # I * I should equal I
    result = I @ I
    assert np.allclose(I.toarray(), result.toarray())
    
    # Diagonal should be all ones
    diag = I.diagonal()
    assert np.all(diag == 1.0)
    assert len(diag) == size
    
    # Off-diagonal should be zeros
    dense = I.toarray()
    for i in range(size):
        for j in range(size):
            if i != j:
                assert dense[i, j] == 0.0


@given(
    size=st.integers(min_value=1, max_value=10),
    density=st.floats(min_value=0.1, max_value=0.9),
)
@settings(max_examples=100)
def test_addition_commutativity(size, density):
    """Test that sparse matrix addition is commutative: A + B = B + A"""
    A = sp.random(size, size, density=density, format='csr', random_state=44)
    B = sp.random(size, size, density=density, format='csr', random_state=45)
    
    # A + B should equal B + A
    sum1 = (A + B).toarray()
    sum2 = (B + A).toarray()
    
    assert np.allclose(sum1, sum2)


@given(
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_zeros_is_additive_identity(rows, cols):
    """Test that zero matrix is additive identity: A + 0 = A"""
    A = sp.random(rows, cols, density=0.5, format='csr', random_state=46)
    Z = sp.csr_matrix((rows, cols))  # Zero matrix
    
    result = A + Z
    assert np.allclose(A.toarray(), result.toarray())


@given(
    m=st.integers(min_value=1, max_value=10),
    k=st.integers(min_value=1, max_value=10), 
    n=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=50)
def test_multiplication_dimensions(m, k, n):
    """Test that matrix multiplication produces correct dimensions."""
    A = sp.random(m, k, density=0.5, format='csr')
    B = sp.random(k, n, density=0.5, format='csr')
    
    C = A @ B
    assert C.shape == (m, n)


@given(
    size=st.integers(min_value=2, max_value=10),
    k=st.integers(min_value=-9, max_value=9),
)
@settings(max_examples=100)
def test_tril_triu_complement(size, k):
    """Test that tril and triu are complements (with overlap on diagonal k)."""
    A = sp.random(size, size, density=0.7, format='csr', random_state=47)
    
    # Get lower and upper triangular parts
    L = sp.tril(A, k=k)
    U = sp.triu(A, k=k+1)  # k+1 to avoid diagonal overlap
    
    # L + U should give back A
    reconstructed = L + U
    assert np.allclose(A.toarray(), reconstructed.toarray())


@given(
    rows=st.integers(min_value=2, max_value=10),
    cols=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100)
def test_vstack_hstack_inverse(rows, cols):
    """Test that vstack and horizontal slicing are inverses."""
    # Create two matrices
    A = sp.random(rows, cols, density=0.5, format='csr', random_state=48)
    B = sp.random(rows, cols, density=0.5, format='csr', random_state=49)
    
    # Stack then split
    stacked = sp.hstack([A, B])
    
    # Extract the parts
    A_recovered = stacked[:, :cols]
    B_recovered = stacked[:, cols:]
    
    assert np.allclose(A.toarray(), A_recovered.toarray())
    assert np.allclose(B.toarray(), B_recovered.toarray())


@given(
    n=st.integers(min_value=1, max_value=10),
    m=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_kron_with_identity(n, m):
    """Test Kronecker product with identity: I_n ⊗ A has block diagonal structure."""
    I_n = sp.eye(n)
    A = sp.random(m, m, density=0.5, format='csr', random_state=50)
    
    result = sp.kron(I_n, A)
    
    # Check dimensions
    assert result.shape == (n*m, n*m)
    
    # Check block diagonal structure
    dense_result = result.toarray()
    dense_A = A.toarray()
    
    for i in range(n):
        # Each block on diagonal should be A
        block = dense_result[i*m:(i+1)*m, i*m:(i+1)*m]
        assert np.allclose(block, dense_A)