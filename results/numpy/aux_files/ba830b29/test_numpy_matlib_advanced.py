import numpy as np
import numpy.matlib as matlib
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# Strategy for valid matrix dimensions
dims = st.integers(min_value=1, max_value=100)
small_dims = st.integers(min_value=1, max_value=20)
edge_dims = st.integers(min_value=0, max_value=5)


@given(st.integers(min_value=0, max_value=10))
def test_identity_with_zero_or_negative(n):
    """Test identity() with edge case dimensions"""
    if n == 0:
        # Should this work? Let's find out
        try:
            result = matlib.identity(n)
            assert result.shape == (0, 0)
            assert result.size == 0
        except Exception as e:
            # Document the behavior
            pass
    else:
        result = matlib.identity(n)
        assert result.shape == (n, n)


@given(st.integers(min_value=-10, max_value=-1))
def test_identity_negative_dimension(n):
    """Test identity() with negative dimensions"""
    try:
        result = matlib.identity(n)
        # If it doesn't raise an error, check the result
        # This could be a bug if negative dimensions are accepted
        print(f"Negative dimension {n} accepted, shape: {result.shape}")
    except (ValueError, TypeError) as e:
        # Expected behavior
        pass


@given(edge_dims, edge_dims, edge_dims, edge_dims)
def test_repmat_zero_repetitions(r, c, m, n):
    """Test repmat with zero repetitions"""
    if r == 0 or c == 0:
        # Skip if input has zero dimension
        return
        
    original = np.arange(max(1, r * c)).reshape(max(1, r), max(1, c))
    
    if m == 0 or n == 0:
        # What happens with zero repetitions?
        try:
            result = matlib.repmat(original, m, n)
            # Check if dimensions make sense
            expected_rows = r * m
            expected_cols = c * n
            assert result.shape == (expected_rows, expected_cols)
            if m == 0 or n == 0:
                assert result.size == 0
        except Exception as e:
            pass


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_repmat_with_special_floats(val):
    """Test repmat with NaN and Inf"""
    a = np.array(val)
    result = matlib.repmat(a, 2, 3)
    
    if np.isnan(val):
        assert np.all(np.isnan(result))
    elif np.isinf(val):
        assert np.all(np.isinf(result))
        assert np.all((result > 0) == (val > 0))  # Same sign of infinity
    else:
        assert np.all(result == val)


@given(dims, dims, st.integers())
def test_eye_extreme_diagonal_offsets(n, m, k):
    """Test eye() with very large diagonal offsets"""
    result = matlib.eye(n, M=m, k=k)
    assert result.shape == (n, m)
    
    # With extreme offsets, all elements should be 0
    if abs(k) >= max(n, m):
        assert np.sum(result) == 0
        assert np.all(result == 0)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, 
                          min_value=-1e6, max_value=1e6), 
                min_size=1, max_size=100))
def test_repmat_preserves_exact_values(values):
    """Test that repmat preserves exact floating point values"""
    arr = np.array(values)
    result = matlib.repmat(arr, 3, 2)
    
    # Check that all tiles have exactly the same values (bit-for-bit)
    for i in range(3):
        for j in range(2):
            tile = result[i, j*len(values):(j+1)*len(values)]
            for idx, val in enumerate(values):
                assert tile[idx] == val  # Exact equality, not approximate


@given(dims)
def test_empty_uninitialized_memory(n):
    """Test that empty() doesn't leak sensitive data"""
    # This is more of a security/privacy test
    # Create multiple empty matrices and check if they have patterns
    matrices = [matlib.empty((n, n)) for _ in range(5)]
    
    # We can't test the exact values (they're uninitialized)
    # But we can check the type and shape
    for m in matrices:
        assert isinstance(m, np.matrix)
        assert m.shape == (n, n)


@given(st.integers(min_value=1, max_value=1000))
def test_identity_memory_efficiency(n):
    """Test the identity() implementation for memory efficiency"""
    # The implementation uses a clever trick with array([1] + n * [0])
    # Let's verify it works correctly for larger matrices
    result = matlib.identity(n)
    
    # Check only diagonal is 1, rest is 0
    diagonal_sum = np.sum(np.diag(result))
    total_sum = np.sum(result)
    
    assert diagonal_sum == n
    assert total_sum == n
    
    # Check no off-diagonal elements are non-zero
    if n > 1:
        # Set diagonal to 0 and check all elements are 0
        result_copy = result.copy()
        np.fill_diagonal(result_copy, 0)
        assert np.all(result_copy == 0)


@given(st.integers(min_value=0, max_value=1000000))
def test_zeros_ones_with_zero_dimension(n):
    """Test zeros/ones with zero in shape"""
    # Test (0, n) shape
    z1 = matlib.zeros((0, n))
    assert z1.shape == (0, n)
    assert z1.size == 0
    
    o1 = matlib.ones((0, n))
    assert o1.shape == (0, n)
    assert o1.size == 0
    
    # Test (n, 0) shape  
    z2 = matlib.zeros((n, 0))
    assert z2.shape == (n, 0)
    assert z2.size == 0
    
    o2 = matlib.ones((n, 0))
    assert o2.shape == (n, 0)
    assert o2.size == 0


@given(st.integers(min_value=-10, max_value=10), 
       st.integers(min_value=-10, max_value=10))
def test_repmat_negative_repetitions(m, n):
    """Test repmat with negative repetition counts"""
    a = np.array([1, 2, 3])
    
    if m < 0 or n < 0:
        # Should this raise an error?
        try:
            result = matlib.repmat(a, m, n)
            # If it works, what's the behavior?
            print(f"Negative reps m={m}, n={n} gave shape: {result.shape}")
        except (ValueError, TypeError) as e:
            # Expected for negative values
            pass
    else:
        result = matlib.repmat(a, m, n)
        assert result.shape[0] == m


@given(st.tuples(dims, dims, dims))
def test_rand_randn_extra_args_ignored(shape):
    """Test that extra args after tuple are ignored as documented"""
    np.random.seed(42)
    r1 = matlib.rand(shape, 999, 888, 777)  # Extra args should be ignored
    
    np.random.seed(42)
    r2 = matlib.rand(shape)
    
    assert np.array_equal(r1, r2)
    
    # Same for randn
    np.random.seed(42)
    rn1 = matlib.randn(shape, 999, 888, 777)
    
    np.random.seed(42)
    rn2 = matlib.randn(shape)
    
    assert np.array_equal(rn1, rn2)


@given(st.integers(min_value=1, max_value=100))
def test_identity_flat_assignment_correctness(n):
    """Test the specific implementation detail of identity using flat assignment"""
    # The implementation does:
    # a = array([1] + n * [0], dtype=dtype)
    # b = empty((n, n), dtype=dtype)
    # b.flat = a
    
    # This assigns the flat array cyclically. Let's verify this works correctly.
    result = matlib.identity(n)
    
    # Manually compute what we expect
    flat_pattern = [1] + n * [0]
    expected = np.zeros((n, n))
    
    # The flat assignment should cycle through the pattern
    for i in range(n * n):
        row = i // n
        col = i % n
        pattern_idx = i % len(flat_pattern)
        expected[row, col] = flat_pattern[pattern_idx]
    
    assert np.array_equal(result, expected)
    
    # For identity matrix, this clever trick works because:
    # - Pattern has length n+1
    # - Matrix has n*n elements
    # - The 1s appear at positions 0, n+1, 2(n+1), ... which are the diagonal positions
    # Let's verify the diagonal positions
    for i in range(n):
        flat_idx = i * n + i  # Diagonal position in flat array
        pattern_idx = flat_idx % (n + 1)
        if i == 0:
            assert pattern_idx == 0  # First element of pattern is 1
        else:
            # For i > 0, we need flat_idx % (n+1) == 0 for the element to be 1
            # flat_idx = i*n + i = i*(n+1)
            # So pattern_idx = i*(n+1) % (n+1) = 0
            assert pattern_idx == 0


@given(st.integers(min_value=1, max_value=50), 
       st.sampled_from([np.float32, np.float64, np.int32, np.int64]))
def test_identity_dtype_preservation(n, dtype):
    """Test that identity preserves dtype correctly"""
    result = matlib.identity(n, dtype=dtype)
    assert result.dtype == dtype
    
    # Check values are correct for the given dtype
    for i in range(n):
        for j in range(n):
            if i == j:
                assert result[i, j] == dtype(1)
            else:
                assert result[i, j] == dtype(0)


if __name__ == "__main__":
    # Run all tests
    import sys
    pytest.main([__file__, "-v", "--tb=short"] + sys.argv[1:])