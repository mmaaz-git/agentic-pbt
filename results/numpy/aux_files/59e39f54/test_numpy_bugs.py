import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.extra import numpy as npst
import math
import sys


# Focus on finding real bugs with more aggressive testing

# Test 1: Testing integer overflow in power operations
@given(st.integers(2, 100), st.integers(2, 100))
def test_power_integer_overflow(base, exp):
    # Test if numpy handles integer overflow correctly
    try:
        result = np.power(base, exp, dtype=np.int64)
        # Python's built-in power for comparison
        expected = base ** exp
        
        # If result fits in int64, it should match
        if expected <= np.iinfo(np.int64).max:
            assert result == expected
    except OverflowError:
        pass  # Expected for large values


# Test 2: Testing edge cases in array indexing with negative indices
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_negative_indexing_consistency(arr):
    if len(arr) > 0:
        # -1 should give last element
        assert arr[-1] == arr[len(arr) - 1]
        # -len should give first element
        assert arr[-len(arr)] == arr[0]


# Test 3: Testing NaN propagation in reduction operations
@given(st.lists(st.floats(allow_nan=True), min_size=1, max_size=10))
def test_nan_propagation_in_sum(lst):
    arr = np.array(lst)
    result = np.sum(arr)
    
    # If there's a NaN, sum should be NaN
    if any(np.isnan(x) for x in lst if not math.isinf(x)):
        assert np.isnan(result)


# Test 4: Testing infinity handling in mean
@given(st.lists(st.floats(allow_infinity=True), min_size=1, max_size=10))
def test_infinity_in_mean(lst):
    arr = np.array(lst)
    
    has_pos_inf = any(x == float('inf') for x in lst)
    has_neg_inf = any(x == float('-inf') for x in lst)
    
    if has_pos_inf and has_neg_inf:
        # inf + -inf should give NaN
        result = np.mean(arr)
        assert np.isnan(result)


# Test 5: Testing empty array edge cases
def test_empty_array_operations():
    empty = np.array([])
    
    # These operations on empty arrays should behave consistently
    with pytest.warns(RuntimeWarning):
        mean_result = np.mean(empty)
        assert np.isnan(mean_result)
    
    # Sum of empty should be 0
    assert np.sum(empty) == 0
    
    # Product of empty should be 1  
    assert np.prod(empty) == 1


# Test 6: Testing zeros and ones with extreme dimensions
@given(st.integers(0, 5), st.integers(0, 5))
def test_zeros_ones_shape(n, m):
    zeros = np.zeros((n, m))
    ones = np.ones((n, m))
    
    assert zeros.shape == (n, m)
    assert ones.shape == (n, m)
    assert np.all(zeros == 0)
    assert np.all(ones == 1)


# Test 7: Testing boolean array indexing edge cases
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_boolean_indexing(arr):
    mask = arr > 0
    positive_elements = arr[mask]
    
    # All selected elements should be positive
    assert np.all(positive_elements > 0) or len(positive_elements) == 0


# Test 8: Testing string array operations
@given(st.lists(st.text(min_size=0, max_size=10), min_size=1, max_size=10))
def test_string_array_operations(strings):
    arr = np.array(strings, dtype=object)
    
    # Check that strings are preserved
    for i, s in enumerate(strings):
        assert arr[i] == s


# Test 9: Testing scalar operations with arrays
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=1, max_dims=2),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_scalar_array_operations(arr, scalar):
    # Scalar operations should broadcast correctly
    added = arr + scalar
    assert added.shape == arr.shape
    
    # Check element-wise operation
    for idx in np.ndindex(arr.shape):
        assert np.isclose(added[idx], arr[idx] + scalar, rtol=1e-10)


# Test 10: Testing view vs copy behavior
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_view_vs_copy(arr):
    # Slicing creates a view
    view = arr[:]
    view[0] = 999.0
    assert arr[0] == 999.0  # Original is modified
    
    # Fancy indexing creates a copy
    original_first = arr[0]
    copy = arr[[0, 1]] if len(arr) > 1 else arr[[0]]
    copy[0] = 888.0
    # Original should not be modified by copy
    # But wait, we modified it above, so it should still be 999.0
    assert arr[0] == 999.0


# Test 11: Testing dtype preservation in operations
@given(npst.arrays(dtype=np.int32, shape=st.integers(1, 100),
                   elements=st.integers(-1000, 1000)))
def test_dtype_preservation(arr):
    # Adding integers should preserve integer dtype
    result = arr + arr
    assert result.dtype == arr.dtype


# Test 12: Testing edge cases in arange
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
       st.floats(allow_nan=False, allow_infinity=False, min_value=0.01, max_value=10))
def test_arange_consistency(start, stop, step):
    if start > stop and step > 0:
        # Should give empty array
        arr = np.arange(start, stop, step)
        assert len(arr) == 0
    elif start < stop and step < 0:
        # Should give empty array
        step = -step  # Make it negative
        arr = np.arange(start, stop, -step)
        assert len(arr) == 0


# Test 13: Testing stack operations
@given(st.lists(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                            elements=st.floats(allow_nan=False, allow_infinity=False)),
                min_size=2, max_size=5))
def test_stack_operations(arrays):
    # Make all arrays same size
    min_len = min(len(a) for a in arrays)
    arrays = [a[:min_len] for a in arrays]
    
    stacked = np.stack(arrays)
    assert stacked.shape == (len(arrays), min_len)
    
    # Check that arrays are preserved
    for i, arr in enumerate(arrays):
        assert np.array_equal(stacked[i], arr)


# Test 14: Testing einsum edge cases with repeated indices
@given(npst.arrays(dtype=np.float64, shape=st.integers(2, 5),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_einsum_self_outer_product(vec):
    # Computing outer product with einsum
    outer = np.einsum('i,i->i', vec, vec)
    expected = vec * vec
    assert np.allclose(outer, expected, rtol=1e-10)


# Test 15: Testing bitwise operations on float arrays (should fail)
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_bitwise_on_floats_fails(arr):
    # Bitwise operations on floats should raise TypeError
    with pytest.raises(TypeError):
        np.bitwise_and(arr, arr)


# Test 16: Testing all and any with empty arrays  
def test_all_any_empty():
    empty = np.array([], dtype=bool)
    
    # all([]) should be True (vacuous truth)
    assert np.all(empty) == True
    
    # any([]) should be False
    assert np.any(empty) == False


# Test 17: Testing concatenate with empty arrays
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_concatenate_with_empty(arr):
    empty = np.array([])
    
    # Concatenating with empty should give original
    result = np.concatenate([arr, empty])
    assert np.array_equal(result, arr)
    
    result2 = np.concatenate([empty, arr])
    assert np.array_equal(result2, arr)


# Test 18: Testing NaN comparison behavior
def test_nan_comparison():
    nan = float('nan')
    arr = np.array([1.0, nan, 3.0])
    
    # NaN comparisons should always be False
    assert not np.any(arr == nan)  # Even NaN != NaN
    
    # But np.isnan should work
    assert np.sum(np.isnan(arr)) == 1


# Test 19: Testing integer division edge cases
@given(st.integers(-100, 100), st.integers(-100, 100))
def test_integer_division(a, b):
    if b == 0:
        return  # Skip division by zero
    
    # NumPy integer division
    np_result = np.floor_divide(a, b)
    
    # Python integer division
    py_result = a // b
    
    assert np_result == py_result


# Test 20: Testing remainder operation consistency
@given(st.integers(-100, 100), st.integers(-100, 100))
def test_remainder_consistency(a, b):
    if b == 0:
        return  # Skip division by zero
    
    np_remainder = np.remainder(a, b)
    py_remainder = a % b
    
    assert np_remainder == py_remainder


# Test 21: Testing that unique preserves NaN correctly
@given(st.lists(st.floats(allow_nan=True), min_size=1, max_size=20))
def test_unique_with_nans(lst):
    arr = np.array(lst)
    unique = np.unique(arr)
    
    # Count NaNs in original
    nan_count_original = np.sum(np.isnan(arr))
    
    # Count NaNs in unique
    nan_count_unique = np.sum(np.isnan(unique))
    
    # If there were NaNs, unique should have exactly one NaN
    if nan_count_original > 0:
        assert nan_count_unique == 1


# Test 22: Testing argmax/argmin with all equal values
@given(st.floats(allow_nan=False, allow_infinity=False),
       st.integers(1, 100))
def test_argmax_argmin_all_equal(value, size):
    arr = np.full(size, value)
    
    # When all values are equal, argmax and argmin should return 0
    assert np.argmax(arr) == 0
    assert np.argmin(arr) == 0


# Test 23: Testing flatten vs ravel behavior
@given(npst.arrays(dtype=np.float64, shape=npst.array_shapes(min_dims=2, max_dims=3),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_flatten_vs_ravel(arr):
    flattened = arr.flatten()
    raveled = arr.ravel()
    
    # Both should give same values
    assert np.array_equal(flattened, raveled)
    
    # flatten returns a copy
    flattened[0] = 999.0
    assert arr.flat[0] != 999.0
    
    # ravel returns a view when possible
    # (but not always - depends on memory layout)


# Test 24: Testing cumulative operations with NaN
@given(st.lists(st.floats(allow_nan=True), min_size=1, max_size=10))
def test_cumsum_with_nan(lst):
    arr = np.array(lst)
    cumsum = np.cumsum(arr)
    
    # Once we hit a NaN, all subsequent values should be NaN
    nan_indices = [i for i, x in enumerate(lst) if np.isnan(x)]
    if nan_indices:
        first_nan = nan_indices[0]
        # All values from first_nan onward should be NaN
        assert all(np.isnan(cumsum[i]) for i in range(first_nan, len(cumsum)))


# Test 25: Testing that operations preserve array subclass
class MyArray(np.ndarray):
    pass

@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_subclass_preservation(arr):
    # Create a subclass instance
    my_arr = arr.view(MyArray)
    
    # Some operations should preserve the subclass
    result = my_arr + 1
    assert isinstance(result, MyArray)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])