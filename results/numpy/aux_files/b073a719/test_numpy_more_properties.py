import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=100),
    st.integers(min_value=-10, max_value=10)
)
def test_roll_preserves_elements(arr, shift):
    """Test that roll just shifts elements, preserving all values"""
    arr = np.array(arr)
    rolled = np.roll(arr, shift)
    
    # Should have same elements, just reordered
    assert len(rolled) == len(arr)
    assert set(arr) == set(rolled) or np.allclose(sorted(arr), sorted(rolled))


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_cumsum_sum_consistency(arr):
    """Test that the last element of cumsum equals sum"""
    arr = np.array(arr)
    cumulative = np.cumsum(arr)
    total = np.sum(arr)
    
    if np.isfinite(total) and len(cumulative) > 0:
        assert np.allclose(cumulative[-1], total), f"cumsum[-1] != sum for array {arr}"


@given(st.lists(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False), min_size=2))
def test_diff_cumsum_inverse(arr):
    """Test that diff and cumsum are inverse operations (almost)"""
    arr = np.array(arr)
    
    # diff then cumsum should recover original (minus first element)
    diffed = np.diff(arr)
    reconstructed = np.cumsum(diffed)
    
    # Should match original array starting from second element (within float precision)
    if len(arr) > 1:
        # Prepend first element to reconstructed
        reconstructed_full = np.concatenate([[arr[0]], arr[0] + reconstructed])
        assert np.allclose(reconstructed_full, arr, rtol=1e-10), "diff/cumsum not inverse"


@given(st.floats(min_value=-89, max_value=89, allow_nan=False))
def test_trigonometric_identity(x):
    """Test sin^2(x) + cos^2(x) = 1"""
    sin_val = np.sin(x)
    cos_val = np.cos(x)
    result = sin_val**2 + cos_val**2
    
    assert np.allclose(result, 1.0, rtol=1e-15), f"sin^2 + cos^2 != 1 for x={x}, got {result}"


@given(st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_exp_log_inverse(x):
    """Test that log(exp(x)) = x for reasonable x values"""
    if x > 0:
        # For positive x, test exp(log(x)) = x
        result = np.exp(np.log(x))
        assert np.allclose(result, x, rtol=1e-14), f"exp(log({x})) = {result}"
    else:
        # For any x, test log(exp(x)) = x (if exp(x) doesn't overflow)
        exp_x = np.exp(x)
        if np.isfinite(exp_x):
            result = np.log(exp_x)
            assert np.allclose(result, x, rtol=1e-14), f"log(exp({x})) = {result}"


@given(st.floats(min_value=0.1, max_value=1000, allow_nan=False))
def test_reciprocal_involution(x):
    """Test that reciprocal(reciprocal(x)) = x"""
    recip1 = np.reciprocal(x)
    recip2 = np.reciprocal(recip1)
    assert np.allclose(recip2, x, rtol=1e-14), f"Double reciprocal of {x} = {recip2}"


@given(st.integers(min_value=-100, max_value=100))
def test_abs_with_integers(x):
    """Test abs with integer inputs"""
    result = np.abs(x)
    expected = abs(x)
    assert result == expected, f"np.abs({x}) = {result}, expected {expected}"


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=100),
    st.floats(min_value=0.01, max_value=0.99)
)
def test_percentile_properties(arr, q):
    """Test percentile properties"""
    arr = np.array(arr)
    q_percent = q * 100  # Convert to percentage
    
    percentile_val = np.percentile(arr, q_percent)
    
    # Property: percentile value should be within array bounds
    assert percentile_val >= np.min(arr), f"Percentile below minimum"
    assert percentile_val <= np.max(arr), f"Percentile above maximum"
    
    # Property: roughly q fraction of values should be <= percentile
    below_count = np.sum(arr <= percentile_val)
    fraction_below = below_count / len(arr)
    
    # Allow some tolerance for small arrays
    if len(arr) > 10:
        assert abs(fraction_below - q) < 0.3, f"Percentile not splitting array correctly"


@given(st.floats(min_value=-1e308, max_value=1e308, allow_nan=False, allow_infinity=False))
def test_sign_properties(x):
    """Test properties of the sign function"""
    sign_x = np.sign(x)
    
    if x > 0:
        assert sign_x == 1, f"sign({x}) should be 1, got {sign_x}"
    elif x < 0:
        assert sign_x == -1, f"sign({x}) should be -1, got {sign_x}"
    else:
        assert sign_x == 0, f"sign(0) should be 0, got {sign_x}"
    
    # Property: sign(x) * abs(x) = x (except for -0.0)
    if x != 0:
        reconstructed = sign_x * np.abs(x)
        assert np.allclose(reconstructed, x), f"sign * abs doesn't reconstruct {x}"


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1))
def test_unique_properties(arr):
    """Test properties of unique function"""
    arr = np.array(arr)
    unique_vals = np.unique(arr)
    
    # Property 1: unique values are sorted
    assert np.array_equal(unique_vals, np.sort(unique_vals)), "Unique values not sorted"
    
    # Property 2: no duplicates in unique
    assert len(unique_vals) == len(set(unique_vals)), "Duplicates in unique values"
    
    # Property 3: all unique values exist in original
    for val in unique_vals:
        assert val in arr, f"Unique value {val} not in original array"


if __name__ == "__main__":
    print("Running additional NumPy property tests...")
    pytest.main([__file__, "-v", "--tb=short"])