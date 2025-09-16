import numpy as np
import pytest
from hypothesis import given, strategies as st, assume, settings, example, note
from hypothesis.extra import numpy as npst
import math
import sys


# More advanced property testing to find bugs

# Test 1: Testing take with out-of-bounds indices and mode parameter
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False)),
       st.lists(st.integers(-20, 20), min_size=1, max_size=10))
def test_take_mode_behavior(arr, indices):
    indices = np.array(indices)
    
    # mode='raise' should raise for out of bounds
    for idx in indices:
        if idx < -len(arr) or idx >= len(arr):
            with pytest.raises(IndexError):
                np.take(arr, indices, mode='raise')
            break
    else:
        # All indices valid
        result = np.take(arr, indices, mode='raise')
        for i, idx in enumerate(indices):
            assert result[i] == arr[idx]
    
    # mode='wrap' should wrap around
    result_wrap = np.take(arr, indices, mode='wrap')
    for i, idx in enumerate(indices):
        wrapped_idx = idx % len(arr)
        assert result_wrap[i] == arr[wrapped_idx]
    
    # mode='clip' should clip to bounds
    result_clip = np.take(arr, indices, mode='clip')
    for i, idx in enumerate(indices):
        clipped_idx = np.clip(idx, 0, len(arr)-1)
        assert result_clip[i] == arr[clipped_idx]


# Test 2: Testing advanced indexing with multiple arrays
@given(npst.arrays(dtype=np.float64, shape=(st.integers(3, 10), st.integers(3, 10)),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_advanced_indexing_consistency(arr):
    rows, cols = arr.shape
    
    # Create index arrays
    row_indices = np.array([0, min(1, rows-1), min(2, rows-1)])[:min(3, rows)]
    col_indices = np.array([0, min(1, cols-1), min(2, cols-1)])[:min(3, cols)]
    
    # Advanced indexing
    result = arr[row_indices[:, None], col_indices]
    
    # Check shape
    assert result.shape == (len(row_indices), len(col_indices))
    
    # Check values
    for i, r in enumerate(row_indices):
        for j, c in enumerate(col_indices):
            assert result[i, j] == arr[r, c]


# Test 3: Testing numpy's handling of structured arrays
@given(st.lists(st.tuples(st.integers(-100, 100), 
                          st.floats(allow_nan=False, allow_infinity=False)),
                min_size=1, max_size=10))
def test_structured_array_operations(data):
    # Create structured array
    dt = np.dtype([('x', 'i4'), ('y', 'f8')])
    arr = np.array(data, dtype=dt)
    
    # Access fields
    x_values = arr['x']
    y_values = arr['y']
    
    # Check values preserved
    for i, (x, y) in enumerate(data):
        assert x_values[i] == x
        assert np.isclose(y_values[i], y, rtol=1e-10)


# Test 4: Testing masked array operations
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)),
       npst.arrays(dtype=bool, shape=st.integers(1, 20)))
def test_masked_array_operations(data, mask):
    # Make same size
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    # Create masked array
    ma = np.ma.masked_array(data, mask=mask)
    
    # Operations should ignore masked values
    if not mask.all():  # If not all masked
        mean = ma.mean()
        # Mean should only consider unmasked values
        expected_mean = data[~mask].mean() if (~mask).any() else 0
        assert np.isclose(mean, expected_mean, rtol=1e-10)


# Test 5: Testing in-place operations preserve memory location
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 100),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)))
def test_inplace_operations(arr):
    original_id = id(arr)
    original_data_ptr = arr.__array_interface__['data'][0]
    
    # In-place operations
    arr += 1
    arr *= 2
    arr -= 3
    
    # Should be same array object
    assert id(arr) == original_id
    assert arr.__array_interface__['data'][0] == original_data_ptr


# Test 6: Testing where with multiple conditions
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_where_multiple_conditions(arr):
    # Complex condition
    condition = (arr > 0) & (arr < 5)
    result = np.where(condition, arr * 2, arr)
    
    for i, val in enumerate(arr):
        if 0 < val < 5:
            assert result[i] == val * 2
        else:
            assert result[i] == val


# Test 7: Testing lexsort behavior
@given(st.lists(st.tuples(st.integers(-10, 10), st.integers(-10, 10)),
                min_size=2, max_size=20))
def test_lexsort_consistency(pairs):
    # Separate into two arrays
    a = np.array([p[0] for p in pairs])
    b = np.array([p[1] for p in pairs])
    
    # Lexsort (sorts by a, then by b)
    indices = np.lexsort((b, a))
    
    # Check ordering
    sorted_pairs = [(a[i], b[i]) for i in indices]
    for i in range(len(sorted_pairs) - 1):
        # Should be lexicographically sorted
        assert sorted_pairs[i] <= sorted_pairs[i+1]


# Test 8: Testing numpy's datetime64 arithmetic
@given(st.integers(0, 1000000), st.integers(-365, 365))
def test_datetime64_arithmetic(base_days, delta_days):
    # Create base datetime
    base = np.datetime64('2020-01-01') + np.timedelta64(base_days, 'D')
    delta = np.timedelta64(delta_days, 'D')
    
    # Add and subtract
    future = base + delta
    reconstructed = future - delta
    
    assert base == reconstructed


# Test 9: Testing numpy's handling of infinity in integer operations
def test_infinity_to_integer_conversion():
    # Converting infinity to integer should raise or saturate
    inf_array = np.array([float('inf'), float('-inf'), 1.0])
    
    # This should handle infinities specially
    with pytest.raises((OverflowError, ValueError)):
        inf_array.astype(np.int64)


# Test 10: Testing reduceat operations
@given(npst.arrays(dtype=np.float64, shape=st.integers(5, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_reduceat_consistency(arr):
    # Define reduction indices
    indices = [0, 2, 5, len(arr)]
    indices = [i for i in indices if i < len(arr)]
    if len(indices) < 2:
        indices = [0]
    
    # Use add.reduceat
    result = np.add.reduceat(arr, indices)
    
    # Verify each segment
    for i in range(len(result)):
        if i < len(indices) - 1:
            start = indices[i]
            end = indices[i+1]
        else:
            start = indices[i]
            end = len(arr)
        
        expected = np.sum(arr[start:end])
        assert np.isclose(result[i], expected, rtol=1e-10)


# Test 11: Testing broadcast_arrays behavior
@given(npst.arrays(dtype=np.float64, shape=st.one_of(st.just((1,)), st.just((5,))),
                   elements=st.floats(allow_nan=False, allow_infinity=False)),
       npst.arrays(dtype=np.float64, shape=st.one_of(st.just((1,)), st.just((5,))),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_broadcast_arrays(a, b):
    try:
        broadcasted = np.broadcast_arrays(a, b)
        
        # Should have same shape after broadcasting
        assert broadcasted[0].shape == broadcasted[1].shape
        
        # Values should be repeated appropriately
        if a.shape == (1,) and b.shape == (5,):
            assert np.all(broadcasted[0] == a[0])
        elif b.shape == (1,) and a.shape == (5,):
            assert np.all(broadcasted[1] == b[0])
    except ValueError:
        # Incompatible shapes for broadcasting
        pass


# Test 12: Testing numpy's handling of subnormal numbers
def test_subnormal_number_handling():
    # Create subnormal numbers (very small numbers close to zero)
    subnormal = np.float64(2.225e-308)  # Close to minimum normal
    tiny = subnormal / 2  # Should be subnormal
    
    # Operations with subnormals
    result = tiny + tiny
    
    # Should handle correctly without underflow to zero
    assert result != 0 or tiny == 0


# Test 13: Testing choice with probabilities
@given(st.integers(2, 10))
@settings(max_examples=10)  # Reduce examples for statistical test
def test_choice_with_probabilities(n):
    # Create non-uniform probabilities
    probs = np.ones(n) / n
    probs[0] = 0.5
    probs[1:] = 0.5 / (n - 1)
    
    # Sample many times
    np.random.seed(42)
    samples = np.random.choice(n, size=10000, p=probs)
    
    # First element should appear roughly 50% of the time
    first_count = np.sum(samples == 0)
    assert 4500 < first_count < 5500  # Allow some variance


# Test 14: Testing pad function with various modes
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 10),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)),
       st.integers(0, 5), st.integers(0, 5))
def test_pad_modes(arr, pad_before, pad_after):
    # Test constant padding
    padded = np.pad(arr, (pad_before, pad_after), mode='constant', constant_values=0)
    assert len(padded) == len(arr) + pad_before + pad_after
    assert np.all(padded[:pad_before] == 0)
    assert np.all(padded[-pad_after:] == 0) if pad_after > 0 else True
    assert np.array_equal(padded[pad_before:pad_before+len(arr)], arr)
    
    # Test edge padding
    if len(arr) > 0:
        padded_edge = np.pad(arr, (pad_before, pad_after), mode='edge')
        if pad_before > 0:
            assert np.all(padded_edge[:pad_before] == arr[0])
        if pad_after > 0:
            assert np.all(padded_edge[-pad_after:] == arr[-1])


# Test 15: Testing numpy's polynomial class
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10),
                min_size=1, max_size=5))
def test_polynomial_operations(coeffs):
    # Create polynomial
    p = np.poly1d(coeffs)
    
    # Evaluate at zero
    result_at_zero = p(0)
    # Should equal the last coefficient (constant term)
    if len(coeffs) > 0:
        assert np.isclose(result_at_zero, coeffs[-1], rtol=1e-10)
    
    # Derivative
    dp = np.polyder(p)
    
    # Check degree reduction
    if len(coeffs) > 1:
        assert len(dp.coefficients) == len(coeffs) - 1 or dp.coefficients[0] == 0


# Test 16: Testing digitize edge cases
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False, min_value=-10, max_value=10)))
def test_digitize_consistency(arr):
    # Create bins
    bins = np.linspace(np.min(arr) - 1, np.max(arr) + 1, 5)
    
    # Digitize
    indices = np.digitize(arr, bins)
    
    # Check that values fall in correct bins
    for i, val in enumerate(arr):
        idx = indices[i]
        if idx == 0:
            assert val < bins[0]
        elif idx == len(bins):
            assert val >= bins[-1]
        else:
            assert bins[idx-1] <= val < bins[idx] or np.isclose(val, bins[idx-1])


# Test 17: Testing extract and place functions
@given(npst.arrays(dtype=np.float64, shape=st.integers(1, 20),
                   elements=st.floats(allow_nan=False, allow_infinity=False)))
def test_extract_place_consistency(arr):
    condition = arr > 0
    
    # Extract values where condition is True
    extracted = np.extract(condition, arr)
    
    # Should only have positive values
    if len(extracted) > 0:
        assert np.all(extracted > 0)
    
    # Place values back
    new_arr = np.zeros_like(arr)
    if len(extracted) > 0:
        np.place(new_arr, condition, extracted)
        
        # Check placement
        for i, cond in enumerate(condition):
            if cond:
                assert new_arr[i] in extracted


# Test 18: Testing numpy's matrix multiplication chain optimization
@given(st.integers(2, 5))
def test_multi_dot_optimization(n):
    # Create chain of matrices with compatible dimensions
    matrices = []
    np.random.seed(42)
    
    dims = [np.random.randint(2, 10) for _ in range(n+1)]
    for i in range(n):
        matrices.append(np.random.randn(dims[i], dims[i+1]))
    
    # Compare multi_dot with sequential multiplication
    result1 = np.linalg.multi_dot(matrices)
    
    result2 = matrices[0]
    for m in matrices[1:]:
        result2 = result2 @ m
    
    assert np.allclose(result1, result2, rtol=1e-10)


# Test 19: Testing numpy's special float values
def test_special_float_values():
    # Test that special values are handled correctly
    special_values = [np.inf, -np.inf, np.nan, 0.0, -0.0]
    arr = np.array(special_values)
    
    # Check positive/negative zero
    assert arr[3] == 0.0
    assert arr[4] == -0.0
    # They should be equal but have different signs
    assert arr[3] == arr[4]
    assert np.signbit(arr[4]) and not np.signbit(arr[3])


# Test 20: Testing fromiter with generator
@given(st.integers(1, 100))
def test_fromiter_consistency(n):
    # Create array from generator
    gen = (i**2 for i in range(n))
    arr = np.fromiter(gen, dtype=np.int64)
    
    # Check values
    expected = np.array([i**2 for i in range(n)])
    assert np.array_equal(arr, expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x", "--hypothesis-show-statistics"])