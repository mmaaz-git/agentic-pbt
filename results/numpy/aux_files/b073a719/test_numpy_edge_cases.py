import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.integers(min_value=-2**63+1, max_value=2**63-1))
def test_abs_integer_overflow(x):
    """Test abs with edge case integers"""
    result = np.abs(x)
    expected = abs(x) if x != -2**63 else 2**63  # Python handles this differently
    
    # For the most negative int64, abs should overflow or handle specially
    if x == -2**63+1:
        # This is -9223372036854775807, whose abs is valid
        assert result == 2**63-1


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_special_value_handling(x):
    """Test how numpy handles special float values"""
    if np.isnan(x):
        # NaN behavior
        assert np.isnan(np.abs(x)), "abs(NaN) should be NaN"
        assert np.isnan(np.square(x)), "square(NaN) should be NaN"
    elif np.isinf(x):
        # Infinity behavior
        assert np.isinf(np.abs(x)), "abs(inf) should be inf"
        assert np.isinf(np.square(x)), "square(inf) should be inf"


@given(st.floats(min_value=-1e-300, max_value=1e-300, allow_nan=False, allow_infinity=False))
def test_sign_with_tiny_numbers(x):
    """Test sign function with very small numbers"""
    sign_val = np.sign(x)
    
    if x > 0:
        assert sign_val == 1.0, f"sign({x}) should be 1"
    elif x < 0:
        assert sign_val == -1.0, f"sign({x}) should be -1"
    else:
        assert sign_val == 0.0, f"sign(0) should be 0"


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=2))
def test_argmax_argmin_ties(arr):
    """Test argmax/argmin behavior with duplicate values"""
    arr = np.array(arr)
    
    # Create an array with guaranteed duplicates
    arr[1] = arr[0]  # Make first two elements the same
    
    if np.all(arr == arr[0]):
        # All elements are the same
        # argmax and argmin should return valid indices
        max_idx = np.argmax(arr)
        min_idx = np.argmin(arr)
        assert 0 <= max_idx < len(arr), "argmax returned invalid index"
        assert 0 <= min_idx < len(arr), "argmin returned invalid index"


@given(
    st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_power_edge_cases(base, exponent):
    """Test power function edge cases"""
    if base == 0 and exponent < 0:
        # 0^(-n) should be inf or raise error
        result = np.power(base, exponent)
        assert np.isinf(result), f"0^{exponent} should be inf, got {result}"
    elif base < 0 and not float(exponent).is_integer():
        # Negative base with non-integer exponent should produce NaN
        result = np.power(base, exponent)
        assert np.isnan(result), f"{base}^{exponent} should be NaN for negative base with non-integer exponent"


@given(st.floats(min_value=0, max_value=1e-300, allow_nan=False, exclude_min=True))
def test_log_tiny_positive(x):
    """Test log with tiny positive numbers"""
    result = np.log(x)
    
    # Log of tiny positive should be large negative
    assert result < 0, f"log({x}) should be negative"
    
    # Verify exp(log(x)) ≈ x
    if result > -700:  # Avoid underflow
        back = np.exp(result)
        if back > 0:
            relative_error = abs(back - x) / x
            assert relative_error < 0.01 or back == 0, f"exp(log({x})) has large error"


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_clip_with_nan_bounds(x):
    """Test clip behavior with NaN bounds"""
    # What happens when clip bounds are NaN?
    result1 = np.clip(x, np.nan, 10)
    result2 = np.clip(x, -10, np.nan)
    result3 = np.clip(x, np.nan, np.nan)
    
    # These should handle NaN gracefully
    assert np.isnan(result1) or result1 == x or result1 <= 10
    assert np.isnan(result2) or result2 == x or result2 >= -10
    assert np.isnan(result3) or result3 == x


@given(st.integers(min_value=1, max_value=10))
def test_zeros_ones_dtype_consistency(size):
    """Test that zeros and ones produce correct dtypes"""
    # Default dtype
    zeros = np.zeros(size)
    ones = np.ones(size)
    
    assert zeros.dtype == np.float64, f"zeros dtype is {zeros.dtype}, expected float64"
    assert ones.dtype == np.float64, f"ones dtype is {ones.dtype}, expected float64"
    
    # Integer dtype
    zeros_int = np.zeros(size, dtype=int)
    ones_int = np.ones(size, dtype=int)
    
    assert zeros_int.dtype == np.dtype('int64') or zeros_int.dtype == np.dtype('int32')
    assert np.all(zeros_int == 0), "zeros with int dtype should all be 0"
    assert np.all(ones_int == 1), "ones with int dtype should all be 1"


@given(st.lists(st.floats(min_value=-1e100, max_value=1e100, allow_nan=False, allow_infinity=False), min_size=2))
def test_mean_median_relationship(arr):
    """Test relationship between mean and median"""
    arr = np.array(arr)
    
    mean_val = np.mean(arr)
    median_val = np.median(arr)
    
    # Both should be within the range of the array
    if np.isfinite(mean_val):
        assert mean_val >= np.min(arr) - 1e-10, "Mean below minimum"
        assert mean_val <= np.max(arr) + 1e-10, "Mean above maximum"
    
    assert median_val >= np.min(arr), "Median below minimum"
    assert median_val <= np.max(arr), "Median above maximum"


if __name__ == "__main__":
    print("Testing NumPy edge cases...")
    pytest.main([__file__, "-v", "--tb=short"])