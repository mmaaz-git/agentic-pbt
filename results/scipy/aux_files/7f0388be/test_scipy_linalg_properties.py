"""Property-based tests for scipy.linalg functions."""

import numpy as np
import scipy.linalg
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Strategy for generating well-conditioned matrices
@st.composite
def matrices(draw, min_size=2, max_size=10):
    """Generate random matrices that are more likely to be well-conditioned."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    m = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Generate with reasonable values to avoid numerical issues
    elements = st.floats(
        min_value=-100, 
        max_value=100,
        allow_nan=False,
        allow_infinity=False,
        width=64
    )
    
    matrix = draw(st.lists(
        st.lists(elements, min_size=m, max_size=m),
        min_size=n, max_size=n
    ))
    
    return np.array(matrix, dtype=np.float64)


@st.composite
def square_matrices(draw, min_size=2, max_size=8):
    """Generate square matrices."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    
    elements = st.floats(
        min_value=-100,
        max_value=100,
        allow_nan=False,
        allow_infinity=False,
        width=64
    )
    
    matrix = draw(st.lists(
        st.lists(elements, min_size=n, max_size=n),
        min_size=n, max_size=n
    ))
    
    return np.array(matrix, dtype=np.float64)


@st.composite  
def invertible_matrices(draw, min_size=2, max_size=8):
    """Generate matrices that are likely to be invertible."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Start with identity and perturb it
    matrix = np.eye(n) * draw(st.floats(min_value=0.5, max_value=10))
    
    # Add some random perturbations
    perturbation = draw(st.lists(
        st.lists(
            st.floats(min_value=-0.3, max_value=0.3, allow_nan=False, allow_infinity=False),
            min_size=n, max_size=n
        ),
        min_size=n, max_size=n
    ))
    
    matrix = matrix + np.array(perturbation)
    return matrix


# Test 1: QR decomposition round-trip property
@given(matrices(min_size=2, max_size=10))
@settings(max_examples=100)
def test_qr_decomposition_round_trip(matrix):
    """Test that Q @ R reconstructs the original matrix."""
    try:
        q, r = scipy.linalg.qr(matrix)
        reconstructed = q @ r
        
        # Check reconstruction
        assert np.allclose(reconstructed, matrix, rtol=1e-10, atol=1e-10), \
            f"QR decomposition failed to reconstruct matrix. Max diff: {np.max(np.abs(reconstructed - matrix))}"
        
        # Test Q is orthogonal (Q @ Q.T = I)
        n = q.shape[0]
        m = min(q.shape)
        if n >= m:  # Full QR
            q_square = q[:, :m]
            should_be_identity = q_square.T @ q_square
            expected_identity = np.eye(m)
            assert np.allclose(should_be_identity, expected_identity, rtol=1e-10, atol=1e-10), \
                "Q is not orthogonal"
                
    except np.linalg.LinAlgError:
        # Some matrices might be singular, that's okay
        pass


# Test 2: LU decomposition round-trip property  
@given(square_matrices(min_size=2, max_size=10))
@settings(max_examples=100)
def test_lu_decomposition_round_trip(matrix):
    """Test that P @ L @ U reconstructs the original matrix."""
    try:
        p, l, u = scipy.linalg.lu(matrix)
        reconstructed = p @ l @ u
        
        assert np.allclose(reconstructed, matrix, rtol=1e-10, atol=1e-10), \
            f"LU decomposition failed. Max diff: {np.max(np.abs(reconstructed - matrix))}"
            
        # Check L is lower triangular
        assert np.allclose(l, np.tril(l), rtol=1e-10, atol=1e-10), \
            "L is not lower triangular"
            
        # Check U is upper triangular
        assert np.allclose(u, np.triu(u), rtol=1e-10, atol=1e-10), \
            "U is not upper triangular"
            
    except np.linalg.LinAlgError:
        pass


# Test 3: Matrix inverse properties
@given(invertible_matrices(min_size=2, max_size=8))
@settings(max_examples=100)
def test_matrix_inverse_properties(matrix):
    """Test that A @ inv(A) = I and inv(A) @ A = I."""
    # Check matrix is actually invertible
    det = scipy.linalg.det(matrix)
    assume(abs(det) > 1e-10)  # Skip near-singular matrices
    
    try:
        inv_matrix = scipy.linalg.inv(matrix)
        n = matrix.shape[0]
        identity = np.eye(n)
        
        # Test A @ inv(A) = I
        product1 = matrix @ inv_matrix
        assert np.allclose(product1, identity, rtol=1e-9, atol=1e-9), \
            f"A @ inv(A) != I. Max diff: {np.max(np.abs(product1 - identity))}"
        
        # Test inv(A) @ A = I  
        product2 = inv_matrix @ matrix
        assert np.allclose(product2, identity, rtol=1e-9, atol=1e-9), \
            f"inv(A) @ A != I. Max diff: {np.max(np.abs(product2 - identity))}"
            
    except np.linalg.LinAlgError:
        pass


# Test 4: Solve function property
@given(invertible_matrices(min_size=2, max_size=8))
@settings(max_examples=100)
def test_solve_equation(A):
    """Test that solve(A, b) gives x such that A @ x = b."""
    det = scipy.linalg.det(A)
    assume(abs(det) > 1e-10)
    
    n = A.shape[0]
    # Generate a random b vector
    b = np.random.randn(n)
    
    try:
        x = scipy.linalg.solve(A, b)
        
        # Check A @ x = b
        result = A @ x
        assert np.allclose(result, b, rtol=1e-9, atol=1e-9), \
            f"solve failed: A @ x != b. Max diff: {np.max(np.abs(result - b))}"
            
    except np.linalg.LinAlgError:
        pass


# Test 5: Hadamard matrix properties
@given(st.integers(min_value=0, max_value=8))
@settings(max_examples=50)
def test_hadamard_matrix_properties(power):
    """Test Hadamard matrix is orthogonal and has entries ±1."""
    n = 2 ** power  # Hadamard matrices require n to be a power of 2
    
    H = scipy.linalg.hadamard(n)
    
    # Check all entries are ±1
    assert np.all(np.abs(H) == 1), "Hadamard matrix has entries other than ±1"
    
    # Check orthogonality: H @ H.T = n * I
    product = H @ H.T
    expected = n * np.eye(n)
    
    assert np.allclose(product, expected, rtol=1e-10, atol=1e-10), \
        f"Hadamard matrix not orthogonal. Max diff: {np.max(np.abs(product - expected))}"


# Test 6: Circulant matrix structure
@given(st.lists(
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    min_size=2, max_size=10
))
@settings(max_examples=100)
def test_circulant_matrix_structure(first_col):
    """Test circulant matrix has the correct circulant structure."""
    first_col = np.array(first_col)
    C = scipy.linalg.circulant(first_col)
    
    n = len(first_col)
    
    # Check first column matches input
    assert np.allclose(C[:, 0], first_col), "First column doesn't match input"
    
    # Check circulant structure: each row is a circular shift of the previous
    for i in range(1, n):
        expected_row = np.roll(C[i-1], 1)
        assert np.allclose(C[i], expected_row), \
            f"Row {i} is not a circular shift of row {i-1}"


# Test 7: Toeplitz matrix structure
@given(
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False), 
             min_size=2, max_size=10),
    st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False), 
             min_size=2, max_size=10)
)
@settings(max_examples=100)
def test_toeplitz_matrix_structure(col, row):
    """Test Toeplitz matrix has constant diagonals."""
    col = np.array(col)
    row = np.array(row)
    
    # Make sure first elements match (as per documentation)
    row[0] = col[0]
    
    T = scipy.linalg.toeplitz(col, row)
    
    # Check first column
    assert np.allclose(T[:, 0], col), "First column doesn't match"
    
    # Check first row (except first element)
    assert np.allclose(T[0, 1:], row[1:]), "First row doesn't match"
    
    # Check constant diagonals
    m, n = T.shape
    # Check main diagonal and above
    for k in range(n):
        diag = np.diag(T, k)
        if len(diag) > 1:
            # All elements on this diagonal should be the same
            assert np.allclose(diag, diag[0]), f"Diagonal {k} is not constant"
    
    # Check below main diagonal
    for k in range(1, m):
        diag = np.diag(T, -k)
        if len(diag) > 1:
            assert np.allclose(diag, diag[0]), f"Diagonal {-k} is not constant"


# Test 8: Pascal matrix properties
@given(st.integers(min_value=2, max_value=10))
@settings(max_examples=50)
def test_pascal_matrix_symmetric(n):
    """Test Pascal matrix properties for symmetric kind."""
    P = scipy.linalg.pascal(n, kind='symmetric')
    
    # Check symmetry
    assert np.allclose(P, P.T), "Pascal matrix (symmetric) is not symmetric"
    
    # Check first row/column are all 1s
    assert np.all(P[0, :] == 1), "First row of Pascal matrix is not all 1s"
    assert np.all(P[:, 0] == 1), "First column of Pascal matrix is not all 1s"
    
    # Check positive definite (all eigenvalues > 0)
    eigenvalues = scipy.linalg.eigvalsh(P)
    assert np.all(eigenvalues > 0), "Pascal matrix is not positive definite"


# Test 9: Matrix pseudo-inverse properties
@given(matrices(min_size=2, max_size=10))
@settings(max_examples=100)
def test_pinv_properties(A):
    """Test Moore-Penrose pseudo-inverse properties."""
    A_pinv = scipy.linalg.pinv(A)
    
    # Test the four Moore-Penrose conditions
    # 1. A @ A_pinv @ A = A
    result1 = A @ A_pinv @ A
    assert np.allclose(result1, A, rtol=1e-9, atol=1e-9), \
        "Moore-Penrose condition 1 failed: A @ A_pinv @ A != A"
    
    # 2. A_pinv @ A @ A_pinv = A_pinv
    result2 = A_pinv @ A @ A_pinv
    assert np.allclose(result2, A_pinv, rtol=1e-9, atol=1e-9), \
        "Moore-Penrose condition 2 failed: A_pinv @ A @ A_pinv != A_pinv"
    
    # 3. (A @ A_pinv) is Hermitian
    product3 = A @ A_pinv
    assert np.allclose(product3, product3.T, rtol=1e-9, atol=1e-9), \
        "Moore-Penrose condition 3 failed: A @ A_pinv is not Hermitian"
    
    # 4. (A_pinv @ A) is Hermitian
    product4 = A_pinv @ A
    assert np.allclose(product4, product4.T, rtol=1e-9, atol=1e-9), \
        "Moore-Penrose condition 4 failed: A_pinv @ A is not Hermitian"


# Test 10: SVD decomposition round-trip
@given(matrices(min_size=2, max_size=10))
@settings(max_examples=100)
def test_svd_round_trip(A):
    """Test that U @ S @ Vt reconstructs the original matrix."""
    U, s, Vt = scipy.linalg.svd(A)
    
    # Reconstruct matrix
    m, n = A.shape
    S = np.zeros((m, n))
    S[:min(m,n), :min(m,n)] = np.diag(s)
    
    reconstructed = U @ S @ Vt
    
    assert np.allclose(reconstructed, A, rtol=1e-10, atol=1e-10), \
        f"SVD failed to reconstruct matrix. Max diff: {np.max(np.abs(reconstructed - A))}"
    
    # Check U is orthogonal
    if m >= n:
        U_reduced = U[:, :n]
        assert np.allclose(U_reduced.T @ U_reduced, np.eye(n), rtol=1e-10, atol=1e-10), \
            "U is not orthogonal"
    
    # Check V is orthogonal
    assert np.allclose(Vt @ Vt.T, np.eye(n), rtol=1e-10, atol=1e-10), \
        "V is not orthogonal"


# Test 11: Cholesky decomposition for positive definite matrices
@given(st.integers(min_value=2, max_value=8))
@settings(max_examples=100)
def test_cholesky_decomposition(n):
    """Test Cholesky decomposition: A = L @ L.T for positive definite A."""
    # Create a positive definite matrix
    X = np.random.randn(n, n)
    A = X @ X.T + np.eye(n)  # Ensure positive definite
    
    L = scipy.linalg.cholesky(A, lower=True)
    
    # Check reconstruction
    reconstructed = L @ L.T
    assert np.allclose(reconstructed, A, rtol=1e-10, atol=1e-10), \
        f"Cholesky failed. Max diff: {np.max(np.abs(reconstructed - A))}"
    
    # Check L is lower triangular
    assert np.allclose(L, np.tril(L), rtol=1e-10, atol=1e-10), \
        "L is not lower triangular"


# Test 12: Block diagonal matrix construction
@given(
    st.lists(
        matrices(min_size=1, max_size=5),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=50)
def test_block_diag_structure(blocks):
    """Test block_diag creates correct block diagonal structure."""
    if not blocks:
        return
    
    result = scipy.linalg.block_diag(*blocks)
    
    # Verify block structure
    row_offset = 0
    col_offset = 0
    
    for block in blocks:
        block = np.atleast_2d(block)
        m, n = block.shape
        
        # Check this block matches
        extracted = result[row_offset:row_offset+m, col_offset:col_offset+n]
        assert np.allclose(extracted, block), \
            f"Block doesn't match at position ({row_offset}, {col_offset})"
        
        # Check zeros outside the block
        # Above the block
        if row_offset > 0:
            above = result[:row_offset, col_offset:col_offset+n]
            assert np.allclose(above, 0), "Non-zero elements above block"
        
        # To the left of the block
        if col_offset > 0:
            left = result[row_offset:row_offset+m, :col_offset]
            assert np.allclose(left, 0), "Non-zero elements to the left of block"
        
        row_offset += m
        col_offset += n


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])