import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.extra import numpy as npst
import math
import sys


# Looking for edge case behaviors that might be bugs

# Test 1: Testing numpy's handling of very small numbers near zero
@given(st.floats(min_value=-sys.float_info.min, max_value=sys.float_info.min))
def test_near_zero_arithmetic(tiny):
    # Operations with numbers very close to zero
    arr = np.array([tiny])
    
    # Square should give positive or zero
    squared = np.square(arr)
    assert squared[0] >= 0
    
    # Adding zero should preserve the value
    result = arr + 0
    assert result[0] == tiny


# Test 2: Testing searchsorted with NaN
def test_searchsorted_with_nan():
    # Array with NaN
    arr = np.array([1.0, 2.0, np.nan, 3.0, 4.0])
    sorted_arr = np.sort(arr)  # NaN goes to the end
    
    # Searching for NaN
    idx = np.searchsorted(sorted_arr, np.nan)
    # This behavior might be unexpected - NaN comparisons are tricky
    
    # Searching for regular value
    idx_2 = np.searchsorted(sorted_arr, 2.0)
    assert sorted_arr[idx_2] == 2.0 or idx_2 == len(sorted_arr)


# Test 3: Testing array equality with NaN
def test_array_equal_with_nan():
    arr1 = np.array([1.0, np.nan, 3.0])
    arr2 = np.array([1.0, np.nan, 3.0])
    
    # array_equal considers NaN != NaN
    assert not np.array_equal(arr1, arr2)
    
    # But array_equiv does the same
    assert not np.array_equiv(arr1, arr2)
    
    # Need special handling for NaN equality
    assert np.allclose(arr1, arr2, equal_nan=True)


# Test 4: Testing in1d with special values
def test_in1d_special_values():
    arr = np.array([1.0, np.nan, np.inf, -np.inf, 2.0])
    test_elements = np.array([np.nan, np.inf])
    
    result = np.in1d(arr, test_elements)
    
    # NaN is tricky - it won't match even itself
    assert not result[1]  # NaN doesn't match NaN
    assert result[2]  # inf matches inf


# Test 5: Testing histogram with weights edge case
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_histogram_weights_sum(arr):
    # Weights that sum to something specific
    weights = np.ones_like(arr) * 2.0
    
    hist, bins = np.histogram(arr, bins=5, weights=weights)
    
    # Sum of histogram should equal sum of weights
    assert np.isclose(np.sum(hist), np.sum(weights), rtol=1e-10)


# Test 6: Testing percentile with method parameter
@given(npst.arrays(dtype=np.float64, shape=st.integers(5, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_percentile_interpolation_methods(arr):
    # Different interpolation methods should give consistent ordering
    methods = ['linear', 'lower', 'higher', 'midpoint', 'nearest']
    
    results = {}
    for method in methods:
        results[method] = np.percentile(arr, 50, method=method)
    
    # All should be between min and max
    for method, value in results.items():
        assert np.min(arr) <= value <= np.max(arr) or np.isclose(value, np.min(arr)) or np.isclose(value, np.max(arr))


# Test 7: Testing bincount with negative values
def test_bincount_negative_values():
    # bincount doesn't accept negative values
    arr = np.array([-1, 0, 1, 2])
    
    with pytest.raises(ValueError):
        np.bincount(arr)


# Test 8: Testing unravel_index edge cases
@given(st.integers(0, 99))
def test_unravel_index_consistency(flat_idx):
    shape = (10, 10)
    
    # Unravel flat index
    multi_idx = np.unravel_index(flat_idx, shape)
    
    # Ravel it back
    flat_again = np.ravel_multi_index(multi_idx, shape)
    
    assert flat_again == flat_idx


# Test 9: Testing put with mode parameter
@given(npst.arrays(dtype=np.float64, shape=st.integers(5, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_put_mode_behavior(arr):
    # Test wrap mode
    arr_copy = arr.copy()
    indices = [len(arr), len(arr) + 1]  # Out of bounds
    values = [999.0, 888.0]
    
    np.put(arr_copy, indices, values, mode='wrap')
    
    # Should wrap around
    assert arr_copy[0] == 999.0
    assert arr_copy[1] == 888.0


# Test 10: Testing numpy's string truncation behavior
def test_string_array_truncation():
    # Create array with fixed-width strings
    arr = np.array(['short', 'a very long string that will be truncated'], dtype='U10')
    
    # Second string should be truncated
    assert arr[1] == 'a very lon'
    assert len(arr[1]) == 10


# Test 11: Testing divmod with arrays
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=100)),
       st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=10))
def test_divmod_consistency(arr, divisor):
    quot, rem = np.divmod(arr, divisor)
    
    # Reconstruction should work
    reconstructed = quot * divisor + rem
    assert np.allclose(reconstructed, arr, rtol=1e-10)


# Test 12: Testing array conversion with overflow
def test_array_creation_overflow():
    # Very large integer that fits in Python int but not in default numpy int
    large_int = 2**100
    
    # This might overflow or change type
    arr = np.array([large_int])
    
    # Check if value is preserved (numpy might use object dtype)
    assert arr[0] == large_int
    # Check dtype - should be object for very large ints
    assert arr.dtype == np.object_


# Test 13: Testing numpy's gcd and lcm
@given(st.integers(1, 1000), st.integers(1, 1000))
def test_gcd_lcm_relationship(a, b):
    gcd = np.gcd(a, b)
    lcm = np.lcm(a, b)
    
    # gcd * lcm = a * b
    assert gcd * lcm == a * b


# Test 14: Testing interp edge cases
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
def test_interp_edge_cases(x):
    # Known points
    xp = np.array([0.0, 1.0, 2.0])
    fp = np.array([0.0, 1.0, 4.0])
    
    # Interpolate
    result = np.interp(x, xp, fp)
    
    # Check bounds
    if x <= 0:
        assert result == 0.0
    elif x >= 2:
        assert result == 4.0
    else:
        # Should be between min and max of fp
        assert 0.0 <= result <= 4.0


# Test 15: Testing piecewise function
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10))
def test_piecewise_function(x):
    # Define conditions and functions
    conditions = [x < 0, (x >= 0) & (x < 5), x >= 5]
    functions = [-1, lambda x: x**2, 25]
    
    result = np.piecewise(x, conditions, functions)
    
    # Verify result
    if x < 0:
        assert result == -1
    elif 0 <= x < 5:
        assert np.isclose(result, x**2, rtol=1e-10)
    else:
        assert result == 25


# Test 16: Testing numpy's sinc function
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
def test_sinc_special_values(x):
    result = np.sinc(x)
    
    # sinc(0) should be 1
    if x == 0:
        assert result == 1.0
    
    # sinc(x) = sin(pi*x) / (pi*x) for x != 0
    if x != 0:
        expected = np.sin(np.pi * x) / (np.pi * x)
        assert np.isclose(result, expected, rtol=1e-10)


# Test 17: Testing unwrap function for phase angles
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_unwrap_consistency(arr):
    # Add 2*pi jumps
    wrapped = np.mod(arr, 2*np.pi)
    
    # Unwrap
    unwrapped = np.unwrap(wrapped)
    
    # The difference between consecutive elements should be less than pi
    if len(unwrapped) > 1:
        diffs = np.diff(unwrapped)
        assert np.all(np.abs(diffs) < np.pi + 0.1)  # Small tolerance


# Test 18: Testing select function
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10))
def test_select_function(x):
    # Multiple conditions
    condlist = [x < -5, (x >= -5) & (x < 0), (x >= 0) & (x < 5), x >= 5]
    choicelist = [-100, -10, 10, 100]
    
    result = np.select(condlist, choicelist, default=0)
    
    # Verify result
    if x < -5:
        assert result == -100
    elif -5 <= x < 0:
        assert result == -10
    elif 0 <= x < 5:
        assert result == 10
    elif x >= 5:
        assert result == 100


# Test 19: Testing numpy's logical functions with empty arrays
def test_logical_operations_empty():
    empty = np.array([], dtype=bool)
    
    # Logical operations on empty arrays
    assert np.logical_and.reduce(empty) == True  # Identity for AND
    assert np.logical_or.reduce(empty) == False  # Identity for OR
    
    # XOR on empty
    assert np.logical_xor.reduce(empty) == False


# Test 20: Testing array setflags
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_setflags_behavior(arr):
    # Make array non-writeable
    arr.setflags(write=False)
    
    # Should not be able to modify
    with pytest.raises(ValueError):
        arr[0] = 999.0
    
    # Make writeable again
    arr.setflags(write=True)
    arr[0] = 999.0  # Should work now
    assert arr[0] == 999.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])