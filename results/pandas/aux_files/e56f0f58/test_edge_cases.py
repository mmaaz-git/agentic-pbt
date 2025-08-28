import numpy as np
import pandas as pd
import pandas.arrays as pa
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


@st.composite
def large_integer_array_strategy(draw):
    """Generate larger IntegerArrays for stress testing."""
    size = draw(st.integers(min_value=100, max_value=1000))
    values = np.random.randint(-10000, 10000, size, dtype=np.int64)
    mask = np.random.choice([True, False], size, p=[0.1, 0.9])
    return pa.IntegerArray(values, mask)


@st.composite
def edge_case_interval_strategy(draw):
    """Generate edge case intervals."""
    size = draw(st.integers(min_value=1, max_value=20))
    closed = draw(st.sampled_from(['left', 'right', 'both', 'neither']))
    
    intervals = []
    for _ in range(size):
        # Include edge cases: zero-width, negative, very large
        case = draw(st.integers(min_value=0, max_value=3))
        if case == 0:  # Zero-width interval
            point = draw(st.floats(allow_nan=False, min_value=-100, max_value=100))
            intervals.append(pd.Interval(point, point, closed=closed))
        elif case == 1:  # Very small interval
            left = draw(st.floats(allow_nan=False, min_value=-100, max_value=100))
            intervals.append(pd.Interval(left, left + 1e-10, closed=closed))
        elif case == 2:  # Large interval
            left = draw(st.floats(allow_nan=False, min_value=-1e6, max_value=1e6))
            width = draw(st.floats(min_value=1e3, max_value=1e6))
            intervals.append(pd.Interval(left, left + width, closed=closed))
        else:  # Normal interval
            left = draw(st.floats(allow_nan=False, min_value=-100, max_value=100))
            width = draw(st.floats(min_value=0.1, max_value=10))
            intervals.append(pd.Interval(left, left + width, closed=closed))
    
    return pa.IntervalArray(intervals)


@given(large_integer_array_strategy())
@settings(max_examples=10)
def test_large_array_memory_consistency(arr):
    """Test operations on large arrays don't corrupt memory."""
    original_len = len(arr)
    
    # Various operations
    sorted_indices = arr.argsort()
    assert len(sorted_indices) == original_len
    
    unique = arr.unique()
    assert len(unique) <= original_len
    
    dropped = arr.dropna()
    assert len(dropped) <= original_len


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
def test_interval_from_arrays_edge_cases(values):
    """Test IntervalArray.from_arrays with edge cases."""
    left = values[:-1]
    right = values[1:]
    
    # Make sure left < right for valid intervals
    for i in range(len(left)):
        if left[i] >= right[i]:
            left[i], right[i] = min(left[i], right[i]), max(left[i], right[i]) + 0.1
    
    arr = pa.IntervalArray.from_arrays(left, right)
    
    assert len(arr) == len(left)
    
    # Check each interval is valid
    for i, interval in enumerate(arr):
        assert interval.left <= interval.right


@given(edge_case_interval_strategy())
def test_interval_array_edge_contains(arr):
    """Test contains behavior at interval edges."""
    for interval in arr:
        # Test edge points
        contains_left = arr.contains(interval.left)
        contains_right = arr.contains(interval.right)
        
        # At least the interval itself should contain its edges based on closed
        idx = list(arr).index(interval)
        
        if interval.closed in ['left', 'both']:
            assert contains_left[idx] == True
        else:
            assert contains_left[idx] == False
            
        if interval.closed in ['right', 'both']:
            assert contains_right[idx] == True
        else:
            assert contains_right[idx] == False


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50))
def test_integer_array_value_counts(values):
    """Test value_counts consistency."""
    mask = [False] * len(values)
    arr = pa.IntegerArray(np.array(values, dtype=np.int64), np.array(mask))
    
    counts = arr.value_counts()
    
    # Total count should equal array length
    assert counts.sum() == len(arr)
    
    # Each unique value should be counted correctly
    from collections import Counter
    expected = Counter(values)
    
    for value, count in expected.items():
        assert counts[counts.index == value].iloc[0] == count


@given(st.integers(min_value=0, max_value=10),
       st.integers(min_value=-100, max_value=100))
def test_integer_array_repeat_consistency(n, value):
    """Test repeat operation."""
    arr = pa.IntegerArray(np.array([value], dtype=np.int64), np.array([False]))
    
    repeated = arr.repeat(n)
    
    assert len(repeated) == n
    if n > 0:
        assert all(repeated[i] == value for i in range(n))


@given(st.lists(st.booleans(), min_size=1, max_size=100))
def test_boolean_array_cumulative_operations(values):
    """Test cumulative operations on BooleanArray."""
    mask = [False] * len(values)
    arr = pa.BooleanArray(np.array(values), np.array(mask))
    
    # cumsum should work
    if hasattr(arr, 'cumsum'):
        cumsum = arr.cumsum()
        assert len(cumsum) == len(arr)
        
        # Verify cumulative sum
        expected_sum = 0
        for i in range(len(arr)):
            expected_sum += int(arr[i])
            assert cumsum[i] == expected_sum


@given(st.floats(allow_nan=False, min_value=-1e10, max_value=1e10))
def test_interval_array_single_point_contains(point):
    """Test contains for single point across different interval types."""
    # Create intervals around the point
    intervals = [
        pd.Interval(point - 1, point + 1, closed='both'),
        pd.Interval(point - 1, point, closed='right'),
        pd.Interval(point, point + 1, closed='left'),
        pd.Interval(point - 0.5, point + 0.5, closed='neither'),
    ]
    
    arr = pa.IntervalArray(intervals)
    contains = arr.contains(point)
    
    # Verify expected containment
    assert contains[0] == True  # both closed, point is inside
    assert contains[1] == True  # right closed, point is the right edge
    assert contains[2] == True  # left closed, point is the left edge
    # Fourth one depends on floating point precision


@given(st.integers(min_value=1, max_value=100))
def test_interval_array_from_breaks_monotonic(n):
    """Test from_breaks with non-monotonic input."""
    # Create non-monotonic breaks
    breaks = list(range(n))
    if n > 2:
        # Swap two elements to break monotonicity
        breaks[n//2], breaks[n//2 + 1] = breaks[n//2 + 1], breaks[n//2]
    
    try:
        arr = pa.IntervalArray.from_breaks(breaks)
        # If it succeeds, it should handle non-monotonic input somehow
        assert len(arr) == len(breaks) - 1
    except ValueError:
        # Should raise for non-monotonic
        pass


@given(st.lists(st.text(min_size=0, max_size=5), min_size=10, max_size=100))
def test_string_array_factorize(values):
    """Test factorize on StringArray."""
    # Add some None values
    for i in range(0, len(values), 5):
        values[i] = None
    
    arr = pa.StringArray._from_sequence(values)
    
    if hasattr(arr, 'factorize'):
        codes, uniques = arr.factorize()
        
        assert len(codes) == len(arr)
        
        # Codes should be valid indices into uniques (except -1 for NA)
        for code in codes:
            if code != -1:
                assert 0 <= code < len(uniques)
        
        # Reconstruction should work
        for i, code in enumerate(codes):
            if code == -1:
                assert pd.isna(arr[i])
            else:
                assert arr[i] == uniques[code]


@given(st.integers(min_value=-1000, max_value=1000),
       st.integers(min_value=1, max_value=100))
def test_integer_array_empty_vs_full_mask(value, size):
    """Test behavior difference between all-masked and no-masked arrays."""
    values = np.full(size, value, dtype=np.int64)
    
    # All masked (all NA)
    all_masked = pa.IntegerArray(values, np.ones(size, dtype=bool))
    
    # None masked (all valid)
    none_masked = pa.IntegerArray(values, np.zeros(size, dtype=bool))
    
    # Operations should handle these differently
    assert all_masked.isna().all()
    assert not none_masked.isna().any()
    
    assert pd.isna(all_masked.min())
    assert none_masked.min() == value
    
    assert len(all_masked.dropna()) == 0
    assert len(none_masked.dropna()) == size