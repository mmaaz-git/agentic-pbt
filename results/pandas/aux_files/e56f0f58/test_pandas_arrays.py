import numpy as np
import pandas as pd
import pandas.arrays as pa
from hypothesis import given, strategies as st, assume, settings
import math
import pytest


@st.composite
def integer_array_strategy(draw):
    """Generate IntegerArray with values and mask."""
    size = draw(st.integers(min_value=0, max_value=100))
    values = draw(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=size, max_size=size))
    mask = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    return pa.IntegerArray(np.array(values, dtype=np.int64), np.array(mask, dtype=bool))


@st.composite
def floating_array_strategy(draw):
    """Generate FloatingArray with values and mask."""
    size = draw(st.integers(min_value=0, max_value=100))
    values = draw(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                           min_size=size, max_size=size))
    mask = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    return pa.FloatingArray(np.array(values, dtype=np.float64), np.array(mask, dtype=bool))


@st.composite
def boolean_array_strategy(draw):
    """Generate BooleanArray with values and mask."""
    size = draw(st.integers(min_value=0, max_value=100))
    values = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    mask = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    return pa.BooleanArray(np.array(values, dtype=bool), np.array(mask, dtype=bool))


@st.composite
def interval_array_strategy(draw):
    """Generate IntervalArray."""
    size = draw(st.integers(min_value=1, max_value=50))
    closed = draw(st.sampled_from(['left', 'right', 'both', 'neither']))
    
    intervals = []
    for _ in range(size):
        left = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
        width = draw(st.floats(min_value=0.01, max_value=10))
        right = left + width
        intervals.append(pd.Interval(left, right, closed=closed))
    
    return pa.IntervalArray(intervals)


@given(integer_array_strategy())
def test_integer_array_dropna_length_invariant(arr):
    """Property: len(dropna()) <= len(original)"""
    dropped = arr.dropna()
    assert len(dropped) <= len(arr)
    
    
@given(floating_array_strategy())
def test_floating_array_dropna_length_invariant(arr):
    """Property: len(dropna()) <= len(original)"""
    dropped = arr.dropna()
    assert len(dropped) <= len(arr)


@given(integer_array_strategy())
def test_integer_array_unique_length_invariant(arr):
    """Property: len(unique()) <= len(original)"""
    unique = arr.unique()
    assert len(unique) <= len(arr)


@given(boolean_array_strategy())
def test_boolean_array_unique_length_invariant(arr):
    """Property: len(unique()) <= len(original)"""
    unique = arr.unique()
    assert len(unique) <= len(arr)


@given(integer_array_strategy())
def test_integer_array_argsort_permutation(arr):
    """Property: argsort returns valid permutation indices"""
    assume(len(arr) > 0)
    indices = arr.argsort()
    
    assert len(indices) == len(arr)
    assert set(indices) == set(range(len(arr)))


@given(floating_array_strategy())
def test_floating_array_argsort_permutation(arr):
    """Property: argsort returns valid permutation indices"""
    assume(len(arr) > 0)
    indices = arr.argsort()
    
    assert len(indices) == len(arr)
    assert set(indices) == set(range(len(arr)))


@given(interval_array_strategy())
def test_interval_array_contains_consistency(arr):
    """Property: if interval contains a point, it should be consistent"""
    assume(len(arr) > 0)
    
    for point in [0.0, 1.0, 50.0, -50.0]:
        contains_result = arr.contains(point)
        assert len(contains_result) == len(arr)
        assert all(isinstance(x, (bool, np.bool_)) for x in contains_result)


@given(interval_array_strategy())
def test_interval_array_overlaps_self(arr):
    """Property: each interval overlaps with itself"""
    assume(len(arr) > 0)
    
    for i, interval in enumerate(arr):
        overlaps = arr.overlaps(interval)
        assert overlaps[i] == True


@given(integer_array_strategy(), integer_array_strategy())
def test_integer_array_equality_reflexive(arr1, arr2):
    """Property: equals should be reflexive (x.equals(x) == True)"""
    assert arr1.equals(arr1)
    
    
@given(floating_array_strategy())
def test_floating_array_copy_independence(arr):
    """Property: copy should create independent array"""
    copy = arr.copy()
    
    assert len(copy) == len(arr)
    assert copy.equals(arr)
    
    if len(arr) > 0:
        original_values = arr._data.copy()
        original_mask = arr._mask.copy()
        
        copy._data[0] = -999999
        
        assert np.array_equal(arr._data, original_values)


@given(boolean_array_strategy())
def test_boolean_array_all_any_consistency(arr):
    """Property: if all() is True, then any() must be True (for non-empty)"""
    if len(arr) > 0:
        if arr.all():
            assert arr.any()


@given(integer_array_strategy())
def test_integer_array_min_max_consistency(arr):
    """Property: min <= max for non-empty arrays without all NA"""
    if len(arr) > 0 and not all(arr.isna()):
        min_val = arr.min()
        max_val = arr.max()
        
        if not pd.isna(min_val) and not pd.isna(max_val):
            assert min_val <= max_val


@given(floating_array_strategy())
def test_floating_array_min_max_consistency(arr):
    """Property: min <= max for non-empty arrays without all NA"""
    if len(arr) > 0 and not all(arr.isna()):
        min_val = arr.min()
        max_val = arr.max()
        
        if not pd.isna(min_val) and not pd.isna(max_val):
            assert min_val <= max_val


@given(integer_array_strategy())
def test_integer_array_fillna_removes_na(arr):
    """Property: fillna should remove all NA values"""
    filled = arr.fillna(0)
    assert not any(filled.isna())
    assert len(filled) == len(arr)


@given(integer_array_strategy())
def test_integer_array_astype_round_trip(arr):
    """Property: converting to float and back should preserve non-NA values"""
    float_arr = arr.astype('Float64')
    back_to_int = float_arr.astype('Int64')
    
    for i in range(len(arr)):
        if not pd.isna(arr[i]):
            assert arr[i] == back_to_int[i]


@given(integer_array_strategy())
def test_integer_array_take_indices(arr):
    """Property: take with valid indices should preserve length"""
    assume(len(arr) > 0)
    
    indices = list(range(len(arr)))
    np.random.shuffle(indices)
    indices = indices[:min(10, len(arr))]
    
    taken = arr.take(indices)
    assert len(taken) == len(indices)


@given(integer_array_strategy())
@settings(max_examples=500)
def test_integer_array_delete_length(arr):
    """Property: delete should reduce length by 1"""
    assume(len(arr) > 0)
    
    index_to_delete = len(arr) // 2
    deleted = arr.delete(index_to_delete)
    assert len(deleted) == len(arr) - 1


@given(boolean_array_strategy())
def test_boolean_array_invert_involution(arr):
    """Property: double negation should return original (for non-NA values)"""
    inverted = ~arr
    double_inverted = ~inverted
    
    for i in range(len(arr)):
        if not pd.isna(arr[i]):
            assert arr[i] == double_inverted[i]


@given(interval_array_strategy())
def test_interval_array_length_consistency(arr):
    """Property: length operations should be consistent"""
    assert len(arr) >= 0
    assert len(arr) == len(list(arr))
    
    if len(arr) > 0:
        assert arr[0] in arr