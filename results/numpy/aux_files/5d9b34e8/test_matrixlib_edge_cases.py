import numpy as np
from hypothesis import given, strategies as st, assume, settings, example
import pytest
import math
import warnings

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# More targeted strategies
empty_like_strings = st.sampled_from(['', ' ', '  ', '\t', '\n', ' \n ', ';', ';;', ' ; '])
malformed_strings = st.sampled_from(['1 2 3; 4 5', '1,2;3,4,5', '[[1,2],[3]]', '1 2; 3 4; 5'])

@given(empty_like_strings)
def test_empty_string_parsing(s):
    """Test matrix creation from empty or whitespace strings"""
    try:
        m = np.matrix(s)
        # If it succeeds, check it's valid
        assert isinstance(m, np.matrix)
        assert m.ndim == 2
    except (ValueError, SyntaxError, IndexError) as e:
        # These are expected for invalid input
        pass


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz[];,. ', min_size=1, max_size=50))
def test_invalid_string_with_letters(s):
    """Test matrix string parsing with non-numeric content"""
    try:
        m = np.matrix(s)
        # If successful, should be valid matrix
        assert isinstance(m, np.matrix)
    except (ValueError, SyntaxError, TypeError, NameError):
        # Expected for non-numeric strings
        pass


def test_bmat_with_empty_blocks():
    """Test bmat with empty matrix blocks"""
    m1 = np.matrix([[1, 2], [3, 4]])
    empty = np.matrix(np.empty((0, 2)))  # 0x2 matrix
    
    # Try to create block matrix with empty block
    try:
        result = np.bmat([[m1], [empty]])
        # Should have shape (2, 2) since empty adds 0 rows
        assert result.shape == (2, 2)
        assert np.allclose(result, m1)
    except ValueError:
        # This might be expected behavior
        pass


def test_bmat_with_mismatched_columns():
    """Test bmat with incompatible block dimensions"""
    m1 = np.matrix([[1, 2], [3, 4]])
    m2 = np.matrix([[5, 6, 7], [8, 9, 10]])  # Different column count
    
    with pytest.raises(ValueError):
        np.bmat([[m1], [m2]])


def test_matrix_string_with_semicolon_only():
    """Test matrix creation from string with only semicolons"""
    test_cases = [';', ';;', ';;;', ' ; ; ']
    for s in test_cases:
        try:
            m = np.matrix(s)
            print(f"String '{s}' created matrix with shape {m.shape}")
        except (ValueError, SyntaxError, IndexError) as e:
            pass  # Expected


def test_matrix_getitem_edge_cases():
    """Test matrix indexing edge cases"""
    m = np.matrix([[1, 2, 3], [4, 5, 6]])
    
    # Single element access should return scalar
    elem = m[0, 0]
    assert np.isscalar(elem)
    
    # Empty slice
    empty = m[0:0, :]
    assert isinstance(empty, np.matrix)
    assert empty.shape == (0, 3)
    
    # Boolean indexing
    mask = np.array([True, False])
    filtered = m[mask]
    assert isinstance(filtered, np.matrix)
    assert filtered.shape == (1, 3)


def test_matrix_power_zero_matrix():
    """Test matrix power on zero matrix"""
    zero = np.matrix(np.zeros((3, 3)))
    
    # 0^0 in matrix context
    result = zero ** 0
    expected = np.eye(3)
    assert np.allclose(result, expected)
    
    # 0^n for n > 0
    result = zero ** 2
    assert np.allclose(result, zero)


def test_matrix_power_large_exponent():
    """Test matrix power with large exponents"""
    # Small matrix to avoid overflow
    m = np.matrix([[0.5, 0.1], [0.1, 0.5]])
    
    # Large positive power
    result = m ** 100
    # Should converge toward zero for this matrix
    assert np.all(np.abs(result) < 1.0)
    
    # Check it's still a matrix
    assert isinstance(result, np.matrix)
    assert result.shape == m.shape


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_matrix_scalar_multiplication(scalar):
    """Test scalar multiplication edge cases"""
    m = np.matrix([[1, 2], [3, 4]])
    
    # Scalar multiplication
    result = m * scalar
    assert isinstance(result, np.matrix)
    assert result.shape == m.shape
    
    # Check commutativity: scalar * matrix
    result2 = scalar * m
    assert np.allclose(result, result2)


def test_matrix_with_complex_numbers():
    """Test matrix operations with complex numbers"""
    m = np.matrix([[1+2j, 3+4j], [5+6j, 7+8j]])
    
    # Basic operations should work
    assert isinstance(m, np.matrix)
    assert m.ndim == 2
    
    # Multiplication
    result = m * m.T.conj()  # Hermitian product
    assert isinstance(result, np.matrix)
    
    # Power
    result = m ** 2
    assert isinstance(result, np.matrix)


def test_matrix_string_with_nested_brackets():
    """Test string parsing with nested bracket structures"""
    test_cases = [
        '[[1, 2], [3, 4]]',
        '[1 2; 3 4]',
        '1 2]; 3 4',
        '[1, 2; 3, 4',
    ]
    
    for s in test_cases:
        try:
            m = np.matrix(s)
            # The first case should work after stripping brackets
            if s == '[[1, 2], [3, 4]]':
                assert m.shape == (2, 2)
        except (ValueError, SyntaxError):
            pass  # Expected for malformed strings


def test_matrix_string_with_scientific_notation():
    """Test matrix string parsing with scientific notation"""
    m = np.matrix('1e2 2e-3; 3.14e1 -4.5e-2')
    assert m.shape == (2, 2)
    assert math.isclose(m[0, 0], 100.0)
    assert math.isclose(m[0, 1], 0.002)
    assert math.isclose(m[1, 0], 31.4)
    assert math.isclose(m[1, 1], -0.045)


def test_asmatrix_with_matrix_input():
    """Test asmatrix doesn't copy when input is already a matrix"""
    m1 = np.matrix([[1, 2], [3, 4]])
    m2 = np.asmatrix(m1)
    
    # Should be the same object (no copy)
    assert m2 is m1
    
    # Modify m1 and check m2 changes
    m1[0, 0] = 99
    assert m2[0, 0] == 99


def test_bmat_string_mode():
    """Test bmat with string input referencing variables"""
    # This tests the string evaluation mode of bmat
    A = np.matrix('1 2; 3 4')
    B = np.matrix('5 6; 7 8')
    
    # Pass string with variable names
    result = np.bmat('A B; B A')
    
    expected = np.matrix([[1, 2, 5, 6],
                          [3, 4, 7, 8],
                          [5, 6, 1, 2],
                          [7, 8, 3, 4]])
    
    assert np.allclose(result, expected)


def test_matrix_flatten_order():
    """Test flatten with different orders"""
    m = np.matrix([[1, 2, 3], [4, 5, 6]])
    
    # C-order (row-major)
    flat_c = m.flatten('C')
    assert isinstance(flat_c, np.matrix)
    assert flat_c.shape == (1, 6)
    assert np.array_equal(flat_c, [[1, 2, 3, 4, 5, 6]])
    
    # F-order (column-major)
    flat_f = m.flatten('F')
    assert isinstance(flat_f, np.matrix)
    assert flat_f.shape == (1, 6)
    assert np.array_equal(flat_f, [[1, 4, 2, 5, 3, 6]])


def test_matrix_squeeze_behavior():
    """Test squeeze behavior on matrices"""
    # Column vector
    col = np.matrix([[1], [2], [3]])
    squeezed = col.squeeze()
    assert isinstance(squeezed, np.matrix)
    assert squeezed.shape == (1, 3)  # Becomes row vector
    
    # Row vector  
    row = np.matrix([[1, 2, 3]])
    squeezed = row.squeeze()
    assert isinstance(squeezed, np.matrix)
    assert squeezed.shape == (1, 3)  # Stays row vector
    
    # Regular matrix
    m = np.matrix([[1, 2], [3, 4]])
    squeezed = m.squeeze()
    assert squeezed.shape == (2, 2)  # Unchanged


def test_matrix_multiplication_with_1d_array():
    """Test matrix multiplication with 1D arrays"""
    m = np.matrix([[1, 2], [3, 4]])
    arr = np.array([5, 6])
    
    # Matrix * 1D array should work and return matrix
    result = m * arr.reshape(-1, 1)
    assert isinstance(result, np.matrix)
    assert result.shape == (2, 1)
    
    # Direct multiplication should also work (promotes to column)
    result2 = m * arr
    assert isinstance(result2, np.matrix)


def test_matrix_inplace_operations():
    """Test in-place operations preserve matrix type"""
    m = np.matrix([[1, 2], [3, 4]], dtype=float)
    
    # In-place multiplication
    m *= 2
    assert isinstance(m, np.matrix)
    assert np.array_equal(m, [[2, 4], [6, 8]])
    
    # In-place power
    m **= 2
    assert isinstance(m, np.matrix)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])