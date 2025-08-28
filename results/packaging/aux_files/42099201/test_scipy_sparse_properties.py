import tempfile
import os
import numpy as np
import scipy.sparse as sp
from hypothesis import given, strategies as st, assume, settings
import pytest


@st.composite
def sparse_matrices(draw, max_size=100, format=None):
    """Generate random sparse matrices for testing."""
    rows = draw(st.integers(min_value=1, max_value=max_size))
    cols = draw(st.integers(min_value=1, max_value=max_size))
    density = draw(st.floats(min_value=0.0, max_value=0.3))
    
    # Generate random sparse matrix
    matrix = sp.random(rows, cols, density=density, format='coo')
    
    if format:
        matrix = matrix.asformat(format)
    
    return matrix


@st.composite
def small_sparse_matrices(draw, max_size=20, format=None):
    """Generate small sparse matrices for expensive operations."""
    rows = draw(st.integers(min_value=1, max_value=max_size))
    cols = draw(st.integers(min_value=1, max_value=max_size))
    density = draw(st.floats(min_value=0.0, max_value=0.5))
    
    matrix = sp.random(rows, cols, density=density, format='coo')
    
    if format:
        matrix = matrix.asformat(format)
    
    return matrix


@given(sparse_matrices(format='csr'))
@settings(max_examples=50)
def test_save_load_roundtrip_csr(matrix):
    """Test that save_npz/load_npz preserves CSR matrices exactly."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save and load the matrix
        sp.save_npz(temp_path, matrix)
        loaded = sp.load_npz(temp_path)
        
        # Check that the loaded matrix equals the original
        assert loaded.shape == matrix.shape
        assert loaded.format == matrix.format
        assert np.allclose(loaded.data, matrix.data)
        assert np.array_equal(loaded.indices, matrix.indices)
        assert np.array_equal(loaded.indptr, matrix.indptr)
    finally:
        os.unlink(temp_path)


@given(sparse_matrices(format='coo'))
@settings(max_examples=50)
def test_save_load_roundtrip_coo(matrix):
    """Test that save_npz/load_npz preserves COO matrices (converts to CSR/CSC)."""
    with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save and load the matrix
        sp.save_npz(temp_path, matrix)
        loaded = sp.load_npz(temp_path)
        
        # COO is converted to CSR on save, check data preservation
        assert loaded.shape == matrix.shape
        # Convert original to same format as loaded for comparison
        original_converted = matrix.tocsr() if loaded.format == 'csr' else matrix.tocsc()
        diff = loaded - original_converted
        assert np.allclose(diff.data, 0) if diff.nnz > 0 else True
    finally:
        os.unlink(temp_path)


@given(sparse_matrices())
def test_tril_triu_reconstruction(matrix):
    """Test that tril(A, k) + triu(A, k+1) reconstructs the original matrix."""
    k = 0  # Use main diagonal
    
    # Get lower and upper triangular parts
    lower = sp.tril(matrix, k=k)
    upper = sp.triu(matrix, k=k+1)
    
    # Reconstruct by adding
    reconstructed = lower + upper
    
    # Check that reconstruction equals original
    diff = reconstructed - matrix
    assert diff.nnz == 0 or np.allclose(diff.data, 0)


@given(sparse_matrices())
def test_tril_triu_disjoint(matrix):
    """Test that tril(A, k-1) and triu(A, k) have no overlapping elements."""
    k = 0
    
    lower = sp.tril(matrix, k=k-1)
    upper = sp.triu(matrix, k=k)
    
    # Convert to COO format to check indices
    lower_coo = lower.tocoo()
    upper_coo = upper.tocoo()
    
    # Create sets of (row, col) pairs
    lower_indices = set(zip(lower_coo.row, lower_coo.col))
    upper_indices = set(zip(upper_coo.row, upper_coo.col))
    
    # Check no overlap
    assert len(lower_indices & upper_indices) == 0


@given(st.lists(small_sparse_matrices(max_size=10), min_size=1, max_size=5))
def test_block_diag_shape(matrices):
    """Test that block_diag creates correct shape."""
    result = sp.block_diag(matrices)
    
    expected_rows = sum(m.shape[0] for m in matrices)
    expected_cols = sum(m.shape[1] for m in matrices)
    
    assert result.shape == (expected_rows, expected_cols)


@given(st.lists(small_sparse_matrices(max_size=10), min_size=1, max_size=5))
def test_block_diag_nnz(matrices):
    """Test that block_diag preserves number of non-zeros."""
    result = sp.block_diag(matrices)
    
    expected_nnz = sum(m.nnz for m in matrices)
    assert result.nnz == expected_nnz


@given(st.integers(min_value=1, max_value=100))
def test_identity_eye_equivalence(n):
    """Test that identity(n) and eye(n) produce equivalent results."""
    identity_matrix = sp.identity(n, format='csr')
    eye_matrix = sp.eye(n, format='csr')
    
    diff = identity_matrix - eye_matrix
    assert diff.nnz == 0


@given(st.integers(min_value=1, max_value=100))
def test_identity_diagonal(n):
    """Test that identity matrix has correct diagonal."""
    identity_matrix = sp.identity(n, format='csr')
    
    # Check shape
    assert identity_matrix.shape == (n, n)
    
    # Check diagonal values
    diagonal = identity_matrix.diagonal()
    assert len(diagonal) == n
    assert np.allclose(diagonal, 1.0)
    
    # Check number of non-zeros
    assert identity_matrix.nnz == n


@given(st.integers(min_value=1, max_value=50),
       st.integers(min_value=1, max_value=50),
       st.integers(min_value=-10, max_value=10))
def test_eye_diagonal_offset(m, n, k):
    """Test that eye matrix has correct diagonal at offset k."""
    eye_matrix = sp.eye(m, n, k=k, format='csr')
    
    # Check shape
    assert eye_matrix.shape == (m, n)
    
    # Count expected number of 1s on the k-th diagonal
    if k >= 0:
        # Diagonal starts at column k
        expected_ones = min(m, n - k) if n > k else 0
    else:
        # Diagonal starts at row -k
        expected_ones = min(m + k, n) if m > -k else 0
    
    expected_ones = max(0, expected_ones)
    
    # Check number of non-zeros
    assert eye_matrix.nnz == expected_ones
    
    # If there are non-zeros, they should all be 1
    if eye_matrix.nnz > 0:
        assert np.allclose(eye_matrix.data, 1.0)


@given(st.lists(sparse_matrices(max_size=20), min_size=2, max_size=5))
def test_hstack_shape(matrices):
    """Test that hstack produces correct shape."""
    # Make all matrices have same number of rows
    n_rows = matrices[0].shape[0]
    matrices_same_rows = []
    for m in matrices:
        if m.shape[0] != n_rows:
            # Resize to have same rows
            resized = sp.csr_matrix((n_rows, m.shape[1]))
            min_rows = min(n_rows, m.shape[0])
            resized[:min_rows, :] = m[:min_rows, :]
            matrices_same_rows.append(resized)
        else:
            matrices_same_rows.append(m)
    
    result = sp.hstack(matrices_same_rows)
    
    expected_rows = n_rows
    expected_cols = sum(m.shape[1] for m in matrices_same_rows)
    
    assert result.shape == (expected_rows, expected_cols)


@given(st.lists(sparse_matrices(max_size=20), min_size=2, max_size=5))
def test_vstack_shape(matrices):
    """Test that vstack produces correct shape."""
    # Make all matrices have same number of columns
    n_cols = matrices[0].shape[1]
    matrices_same_cols = []
    for m in matrices:
        if m.shape[1] != n_cols:
            # Resize to have same cols
            resized = sp.csr_matrix((m.shape[0], n_cols))
            min_cols = min(n_cols, m.shape[1])
            resized[:, :min_cols] = m[:, :min_cols]
            matrices_same_cols.append(resized)
        else:
            matrices_same_cols.append(m)
    
    result = sp.vstack(matrices_same_cols)
    
    expected_rows = sum(m.shape[0] for m in matrices_same_cols)
    expected_cols = n_cols
    
    assert result.shape == (expected_rows, expected_cols)