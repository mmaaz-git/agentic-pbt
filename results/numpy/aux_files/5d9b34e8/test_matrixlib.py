import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Strategy for valid matrix data
matrix_data = st.lists(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        min_size=1, max_size=10
    ),
    min_size=1, max_size=10
).filter(lambda rows: len(set(len(row) for row in rows)) == 1)  # All rows same length

small_matrix_data = st.lists(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
        min_size=1, max_size=4
    ),
    min_size=1, max_size=4
).filter(lambda rows: len(set(len(row) for row in rows)) == 1)

# Strategy for square matrices (for power operations)
square_matrix_data = st.lists(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10),
        min_size=1, max_size=3
    ),
    min_size=1, max_size=3
).filter(lambda rows: len(rows) == len(rows[0]) and all(len(row) == len(rows) for row in rows))


@given(matrix_data)
def test_asmatrix_round_trip(data):
    """Test that asmatrix preserves data when converting from list"""
    m = np.asmatrix(data)
    assert m.shape[0] == len(data)
    assert m.shape[1] == len(data[0])
    # Check data is preserved
    result = m.tolist()
    for i in range(len(data)):
        for j in range(len(data[0])):
            assert math.isclose(result[i][j], data[i][j], rel_tol=1e-9)


@given(matrix_data)
def test_matrix_always_2d(data):
    """Test that matrix objects always remain 2D"""
    m = np.matrix(data)
    assert m.ndim == 2
    # Even after operations
    squeezed = m.squeeze()
    assert squeezed.ndim == 2
    flattened = m.flatten()
    assert flattened.ndim == 2


@given(small_matrix_data)
def test_matrix_string_parsing_round_trip(data):
    """Test matrix creation from string representation"""
    m1 = np.matrix(data)
    # Create string representation
    rows = []
    for row in data:
        rows.append(' '.join(str(x) for x in row))
    str_repr = '; '.join(rows)
    
    # Parse back
    m2 = np.matrix(str_repr)
    
    # Compare shapes
    assert m1.shape == m2.shape
    
    # Compare values (with tolerance for float parsing)
    for i in range(m1.shape[0]):
        for j in range(m1.shape[1]):
            assert math.isclose(m1[i, j], m2[i, j], rel_tol=1e-6, abs_tol=1e-10)


@given(square_matrix_data, st.integers(min_value=0, max_value=3))
def test_matrix_power_consistency(data, power):
    """Test matrix power operation consistency"""
    m = np.matrix(data)
    
    # Compute power
    result = m ** power
    
    # Check shape preservation
    assert result.shape == m.shape
    
    # For power 0, should be identity
    if power == 0:
        expected = np.eye(m.shape[0])
        assert np.allclose(result, expected)
    
    # For power 1, should be unchanged
    elif power == 1:
        assert np.allclose(result, m)
    
    # For power 2, should equal m * m
    elif power == 2:
        expected = m * m
        assert np.allclose(result, expected)


@given(matrix_data)
def test_matrix_multiplication_shape(data):
    """Test that matrix multiplication preserves matrix type"""
    m = np.matrix(data)
    # Multiply by transpose to ensure compatible dimensions
    result = m * m.T
    assert isinstance(result, np.matrix)
    assert result.ndim == 2
    assert result.shape == (m.shape[0], m.shape[0])


@given(matrix_data)
def test_matrix_sum_shape_preservation(data):
    """Test that sum operations preserve matrix structure"""
    m = np.matrix(data)
    
    # Sum along axis should return matrix
    sum0 = m.sum(axis=0)
    assert isinstance(sum0, np.matrix)
    assert sum0.ndim == 2
    assert sum0.shape == (1, m.shape[1])
    
    sum1 = m.sum(axis=1)
    assert isinstance(sum1, np.matrix)
    assert sum1.ndim == 2
    assert sum1.shape == (m.shape[0], 1)
    
    # Total sum should be scalar
    total = m.sum()
    assert np.isscalar(total)


@given(small_matrix_data, small_matrix_data)
def test_bmat_construction(data1, data2):
    """Test block matrix construction"""
    assume(len(data1[0]) == len(data2[0]))  # Same number of columns
    
    m1 = np.matrix(data1)
    m2 = np.matrix(data2)
    
    # Create block matrix vertically
    result = np.bmat([[m1], [m2]])
    
    assert isinstance(result, np.matrix)
    assert result.shape == (m1.shape[0] + m2.shape[0], m1.shape[1])
    
    # Check values are preserved
    assert np.allclose(result[:m1.shape[0], :], m1)
    assert np.allclose(result[m1.shape[0]:, :], m2)


@given(st.text(alphabet='0123456789. ;,-', min_size=1, max_size=100))
def test_matrix_string_parsing_robustness(text):
    """Test that matrix string parsing handles various inputs"""
    try:
        m = np.matrix(text)
        # If successful, it should be a 2D matrix
        assert isinstance(m, np.matrix)
        assert m.ndim == 2
    except (ValueError, SyntaxError):
        # These exceptions are expected for invalid input
        pass


@given(matrix_data)
def test_matrix_getitem_preserves_2d(data):
    """Test that matrix indexing preserves 2D nature when appropriate"""
    m = np.matrix(data)
    
    # Getting a row should return 2D matrix
    row = m[0]
    assert isinstance(row, np.matrix)
    assert row.ndim == 2
    assert row.shape == (1, m.shape[1])
    
    # Getting a column should return 2D matrix
    if m.shape[1] > 0:
        col = m[:, 0]
        assert isinstance(col, np.matrix)
        assert col.ndim == 2
        assert col.shape == (m.shape[0], 1)


@given(square_matrix_data)
def test_matrix_power_inverse(data):
    """Test matrix power with negative exponents"""
    m = np.matrix(data)
    
    # Check if matrix is invertible (non-zero determinant)
    try:
        det = np.linalg.det(m)
        assume(abs(det) > 1e-10)  # Skip singular matrices
        
        # Test that m^(-1) * m = I
        m_inv = m ** -1
        result = m_inv * m
        identity = np.eye(m.shape[0])
        
        assert np.allclose(result, identity, rtol=1e-5, atol=1e-8)
        
        # Test that m^(-2) = (m^-1)^2
        m_inv2 = m ** -2
        expected = m_inv * m_inv
        assert np.allclose(m_inv2, expected, rtol=1e-5, atol=1e-8)
        
    except (np.linalg.LinAlgError, ValueError):
        # Expected for singular matrices
        pass


@given(matrix_data, matrix_data)
def test_matrix_multiplication_associativity(data1, data2):
    """Test associativity of matrix multiplication"""
    m1 = np.matrix(data1)
    m2 = np.matrix(data2)
    
    # For associativity test, we need compatible dimensions
    # Use transposes to ensure compatibility
    a = m1
    b = m1.T
    c = m1
    
    # Test (a * b) * c == a * (b * c)
    left = (a * b) * c
    right = a * (b * c)
    
    assert np.allclose(left, right, rtol=1e-5, atol=1e-8)


@given(st.lists(st.lists(st.floats(allow_nan=True, allow_infinity=True), min_size=1), min_size=1))
def test_matrix_with_special_values(data):
    """Test matrix behavior with NaN and Inf values"""
    # Ensure rectangular
    if data and all(len(row) == len(data[0]) for row in data):
        m = np.matrix(data)
        assert isinstance(m, np.matrix)
        assert m.ndim == 2
        
        # Operations should not crash
        _ = m.T
        _ = m.flatten()
        _ = m.tolist()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])