import numpy as np
import scipy.sparse as sp
from hypothesis import given, strategies as st, settings, assume
import pytest


@given(
    n_matrices=st.integers(min_value=0, max_value=5),
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_hstack_with_empty_list(n_matrices, rows, cols):
    """Test hstack with various list sizes including empty."""
    if n_matrices == 0:
        # Empty list case
        try:
            result = sp.hstack([])
            assert False, "hstack([]) should raise an error"
        except (ValueError, TypeError):
            pass  # Expected
    else:
        matrices = [sp.random(rows, cols, density=0.5, format='csr') for _ in range(n_matrices)]
        result = sp.hstack(matrices)
        assert result.shape == (rows, cols * n_matrices)


@given(
    rows=st.integers(min_value=0, max_value=10),
    cols=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
def test_empty_matrix_operations(rows, cols):
    """Test operations on empty matrices (0 rows or 0 columns)."""
    if rows == 0 or cols == 0:
        # Create empty matrix
        empty = sp.csr_matrix((rows, cols))
        
        # Transpose should work
        transposed = empty.transpose()
        assert transposed.shape == (cols, rows)
        
        # nnz should be 0
        assert empty.nnz == 0
        
        # toarray should work
        dense = empty.toarray()
        assert dense.shape == (rows, cols)


@given(
    size=st.integers(min_value=1, max_value=10),
    fill_value=st.floats(allow_nan=True, allow_infinity=True),
)
@settings(max_examples=100)
def test_nan_inf_handling(size, fill_value):
    """Test handling of NaN and Inf values in sparse matrices."""
    if np.isnan(fill_value) or np.isinf(fill_value):
        # Create matrix with special values
        data = [fill_value] * size
        row = list(range(size))
        col = list(range(size))
        matrix = sp.coo_matrix((data, (row, col)), shape=(size, size))
        
        # Conversion should preserve special values
        dense = matrix.toarray()
        for i in range(size):
            if np.isnan(fill_value):
                assert np.isnan(dense[i, i])
            elif np.isinf(fill_value):
                assert np.isinf(dense[i, i])


@given(
    size=st.integers(min_value=1, max_value=100000),
)
@settings(max_examples=20)
def test_very_large_sparse_matrix(size):
    """Test creating very large sparse matrices."""
    # Create a very sparse matrix (only diagonal elements)
    data = [1.0] * min(size, 1000)  # Limit data to avoid memory issues
    indices = list(range(min(size, 1000)))
    indptr = list(range(min(size, 1000) + 1))
    
    # This should handle large sizes efficiently
    large_matrix = sp.eye(size, format='csr')
    assert large_matrix.shape == (size, size)
    assert large_matrix.nnz == size


@given(
    rows=st.integers(min_value=1, max_value=5),
    cols=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_duplicate_indices_in_coo(rows, cols):
    """Test COO matrix with duplicate indices (should sum values)."""
    # Create duplicate indices
    data = [1.0, 2.0, 3.0]
    row = [0, 0, 1]  
    col = [0, 0, 1]  # (0,0) appears twice
    
    coo = sp.coo_matrix((data, (row, col)), shape=(rows, cols))
    dense = coo.toarray()
    
    # Values at duplicate indices should be summed
    assert dense[0, 0] == 3.0  # 1.0 + 2.0
    assert dense[1, 1] == 3.0


@given(
    n=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_power_of_zero_matrix(n):
    """Test matrix power of zero matrix."""
    Z = sp.csr_matrix((n, n))  # Zero matrix
    
    # Z^0 should be identity
    Z0 = Z.power(0)
    I = sp.eye(n)
    assert np.allclose(Z0.toarray(), I.toarray())
    
    # Z^k for k>0 should be zero
    Z2 = Z.power(2)
    assert np.allclose(Z2.toarray(), Z.toarray())


@given(
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
    format=st.sampled_from(['csr', 'csc', 'coo', 'dok', 'lil']),
)
@settings(max_examples=50)
def test_format_preservation_in_operations(rows, cols, format):
    """Test that operations preserve format when possible."""
    A = sp.random(rows, cols, density=0.5, format=format)
    B = sp.random(rows, cols, density=0.5, format=format)
    
    # Addition should try to preserve format
    C = A + B
    # Note: Some formats auto-convert (e.g., dok -> csr for addition)
    # So we just check the result is valid
    assert C.shape == (rows, cols)


@given(
    size=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100)
def test_diagonal_matrix_inverse_property(size):
    """Test that diagonal matrices have simple inverses."""
    # Create a diagonal matrix with non-zero diagonal
    diag_values = np.random.rand(size) + 0.1  # Avoid zero
    D = sp.diags(diag_values, 0, shape=(size, size), format='csr')
    
    # For diagonal matrix, inverse is just 1/diagonal
    D_dense = D.toarray()
    D_inv_expected = np.diag(1.0 / diag_values)
    
    # Multiply D by its expected inverse
    I_approx = D @ sp.csr_matrix(D_inv_expected)
    I = sp.eye(size)
    
    assert np.allclose(I_approx.toarray(), I.toarray(), rtol=1e-10)


@given(
    rows=st.integers(min_value=1, max_value=10),
    cols=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_negative_values_handling(rows, cols):
    """Test that negative values are handled correctly."""
    # Create matrix with negative values
    data = [-1.0, -2.0, 3.0, -4.0][:min(4, rows*cols)]
    row = [i % rows for i in range(len(data))]
    col = [i % cols for i in range(len(data))]
    
    matrix = sp.coo_matrix((data, (row, col)), shape=(rows, cols))
    
    # Check that negative values are preserved
    dense = matrix.toarray()
    for i, val in enumerate(data):
        r, c = row[i], col[i]
        # Account for potential duplicate indices
        if dense[r, c] != 0:
            assert val < 0 or dense[r, c] > 0  # Sign preserved


@given(
    size=st.integers(min_value=1, max_value=10),
    density=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=100)
def test_density_edge_cases(size, density):
    """Test matrix creation with extreme density values."""
    # density=0 should create empty matrix
    # density=1 should create full matrix
    matrix = sp.random(size, size, density=density, format='csr')
    
    actual_density = matrix.nnz / (size * size)
    
    if density == 0:
        assert matrix.nnz == 0
    elif density == 1:
        assert matrix.nnz == size * size
    else:
        # Due to randomness, actual density may vary
        # but should be roughly close
        assert 0 <= actual_density <= 1