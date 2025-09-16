import numpy as np
import numpy.matlib as matlib
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.integers(min_value=1, max_value=100))
def test_identity_flat_cycle_bug(n):
    """Test if identity() implementation has issues with its flat assignment"""
    result = matlib.identity(n)
    
    # The implementation uses:
    # a = array([1] + n * [0])  # Length n+1
    # b.flat = a  # Assigns cyclically
    
    # This works because diagonal positions in flat array are 0, n+1, 2(n+1), ...
    # and these all map to index 0 in the pattern (since i*(n+1) % (n+1) = 0)
    
    # But what if we test edge cases?
    # Actually the math works out perfectly, so let's verify
    expected = np.eye(n)
    assert np.array_equal(result, expected)


@given(st.integers(min_value=0, max_value=5), 
       st.integers(min_value=0, max_value=5))
def test_repmat_with_zero_dimensions(m, n):
    """Test repmat behavior with zero in repetition counts"""
    arr = np.array([1, 2, 3])
    result = matlib.repmat(arr, m, n)
    
    # Expected: m rows, each containing n repetitions of the array
    assert result.shape == (m, n * 3)
    
    if m == 0 or n == 0:
        assert result.size == 0
    else:
        # Verify values
        for i in range(m):
            for j in range(n):
                segment = result[i, j*3:(j+1)*3]
                assert np.array_equal(segment, [1, 2, 3])


@given(st.integers(min_value=-100, max_value=-1))
def test_ones_negative_dimension(n):
    """Test ones() with negative dimension"""
    try:
        result = matlib.ones(n)
        # If this succeeds, it's likely a bug
        print(f"Bug: ones({n}) returned shape {result.shape}")
        assert False, f"ones() accepted negative dimension {n}"
    except (ValueError, TypeError):
        # Expected behavior
        pass


@given(st.integers(min_value=-100, max_value=-1))
def test_zeros_negative_dimension(n):
    """Test zeros() with negative dimension"""
    try:
        result = matlib.zeros(n)
        # If this succeeds, it's likely a bug
        print(f"Bug: zeros({n}) returned shape {result.shape}")
        assert False, f"zeros() accepted negative dimension {n}"
    except (ValueError, TypeError):
        # Expected behavior
        pass


@given(st.integers(min_value=-100, max_value=-1))
def test_empty_negative_dimension(n):
    """Test empty() with negative dimension"""
    try:
        result = matlib.empty(n)
        # If this succeeds, it's likely a bug
        print(f"Bug: empty({n}) returned shape {result.shape}")
        assert False, f"empty() accepted negative dimension {n}"
    except (ValueError, TypeError):
        # Expected behavior
        pass


@given(st.integers(min_value=-10, max_value=-1), 
       st.integers(min_value=-10, max_value=-1))
def test_repmat_negative_repetitions(m, n):
    """Test repmat with negative repetition values"""
    arr = np.array([1, 2, 3])
    
    try:
        result = matlib.repmat(arr, m, n)
        # If it works with negative values, document the behavior
        print(f"repmat with m={m}, n={n} gave shape: {result.shape}")
        print(f"Result size: {result.size}")
        
        # Check if it treats negative as 0
        if result.size == 0:
            print("Negative values treated as 0")
        else:
            print(f"Unexpected: non-empty result with negative reps")
            print(f"Result:\n{result}")
            
    except (ValueError, TypeError) as e:
        # This would be expected behavior
        pass


@given(st.integers(min_value=1, max_value=10))
def test_eye_identity_equivalence(n):
    """For square matrices with k=0, eye should equal identity"""
    eye_result = matlib.eye(n, M=n, k=0)
    identity_result = matlib.identity(n)
    
    assert np.array_equal(eye_result, identity_result)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_ones_shape_float(x):
    """Test ones() with float shape - should fail"""
    try:
        result = matlib.ones(x)
        # If this works, check what happens
        if x == int(x) and x > 0:
            # Might be acceptable if float is actually an integer
            assert result.shape == (1, int(x))
        else:
            print(f"Bug: ones({x}) accepted float, returned shape {result.shape}")
    except (TypeError, ValueError):
        # Expected for non-integer shapes
        pass


@given(st.integers(min_value=0, max_value=10))
def test_identity_zero_size(n):
    """Test identity with n=0"""
    if n == 0:
        result = matlib.identity(0)
        assert result.shape == (0, 0)
        assert result.size == 0
        # Check it's still a matrix type
        assert isinstance(result, np.matrix)


@given(st.integers(min_value=1, max_value=100),
       st.integers(min_value=1, max_value=100))
def test_empty_initialization(m, n):
    """Test that empty() really doesn't initialize values"""
    # Create multiple empty matrices
    results = []
    for _ in range(3):
        result = matlib.empty((m, n))
        results.append(result.copy())
    
    # We can't test exact values, but we can verify:
    # 1. They're all matrices
    # 2. They have the right shape
    for r in results:
        assert isinstance(r, np.matrix)
        assert r.shape == (m, n)
    
    # Note: We can't reliably test that values are uninitialized
    # because memory might be reused and contain the same values


@given(st.integers(min_value=1, max_value=10))
def test_identity_immutability_check(n):
    """Check if modifying identity matrix affects future calls"""
    # Get first identity matrix
    i1 = matlib.identity(n)
    i1_copy = i1.copy()
    
    # Modify it
    if n > 0:
        i1[0, 0] = 999
    
    # Get another identity matrix
    i2 = matlib.identity(n)
    
    # i2 should not be affected by modifications to i1
    assert np.array_equal(i2, i1_copy)
    assert i2[0, 0] == 1


if __name__ == "__main__":
    # Run with more examples to find edge cases
    import sys
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"] + sys.argv[1:])