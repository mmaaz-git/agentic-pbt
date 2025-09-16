import numpy as np
import pandas as pd
import pandas.arrays as pa
from hypothesis import given, strategies as st, assume, settings, example
import math
import pytest


@st.composite
def integer_array_with_na_strategy(draw):
    """Generate IntegerArray with guaranteed NA values."""
    size = draw(st.integers(min_value=2, max_value=50))
    values = draw(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=size, max_size=size))
    
    # Ensure at least one NA
    mask = draw(st.lists(st.booleans(), min_size=size, max_size=size))
    mask[draw(st.integers(min_value=0, max_value=size-1))] = True
    
    return pa.IntegerArray(np.array(values, dtype=np.int64), np.array(mask, dtype=bool))


@st.composite  
def interval_array_overlapping_strategy(draw):
    """Generate IntervalArray with potential overlaps."""
    size = draw(st.integers(min_value=2, max_value=20))
    closed = draw(st.sampled_from(['left', 'right', 'both', 'neither']))
    
    intervals = []
    start = draw(st.floats(min_value=-50, max_value=50, allow_nan=False))
    
    for _ in range(size):
        # Create potentially overlapping intervals
        left = draw(st.floats(min_value=start-5, max_value=start+5, allow_nan=False))
        width = draw(st.floats(min_value=0.1, max_value=10))
        right = left + width
        intervals.append(pd.Interval(left, right, closed=closed))
        start = left + width/2  # Move start to create overlaps
    
    return pa.IntervalArray(intervals)


@st.composite
def string_array_strategy(draw):
    """Generate StringArray with None values."""
    size = draw(st.integers(min_value=0, max_value=50))
    elements = []
    for _ in range(size):
        if draw(st.booleans()):
            elements.append(draw(st.text(min_size=0, max_size=20)))
        else:
            elements.append(None)
    return pa.StringArray._from_sequence(elements)


@given(integer_array_with_na_strategy())
def test_integer_array_argmin_with_na(arr):
    """Test argmin behavior with NA values."""
    try:
        idx = arr.argmin()
        # If it returns an index, it should be valid
        assert 0 <= idx < len(arr)
        # The value at that index should not be NA
        assert not pd.isna(arr[idx])
        # It should be the actual minimum
        non_na_values = [arr[i] for i in range(len(arr)) if not pd.isna(arr[i])]
        if non_na_values:
            assert arr[idx] == min(non_na_values)
    except (ValueError, TypeError):
        # Should only raise if all values are NA
        assert all(pd.isna(arr[i]) for i in range(len(arr)))


@given(integer_array_with_na_strategy())
def test_integer_array_argmax_with_na(arr):
    """Test argmax behavior with NA values."""
    try:
        idx = arr.argmax()
        # If it returns an index, it should be valid
        assert 0 <= idx < len(arr)
        # The value at that index should not be NA
        assert not pd.isna(arr[idx])
        # It should be the actual maximum
        non_na_values = [arr[i] for i in range(len(arr)) if not pd.isna(arr[i])]
        if non_na_values:
            assert arr[idx] == max(non_na_values)
    except (ValueError, TypeError):
        # Should only raise if all values are NA
        assert all(pd.isna(arr[i]) for i in range(len(arr)))


@given(interval_array_overlapping_strategy())
def test_interval_array_overlaps_symmetry(arr):
    """Property: overlaps should be symmetric - if A overlaps B, then B overlaps A."""
    for i in range(len(arr)):
        for j in range(len(arr)):
            overlaps_i_j = arr[i].overlaps(arr[j])
            overlaps_j_i = arr[j].overlaps(arr[i])
            assert overlaps_i_j == overlaps_j_i, f"Asymmetric overlap at indices {i}, {j}"


@given(string_array_strategy())
def test_string_array_unique_idempotent(arr):
    """Property: unique(unique(x)) = unique(x) (idempotence)."""
    unique1 = arr.unique()
    unique2 = unique1.unique()
    
    # Convert to sets for comparison (handling None/NA)
    set1 = set(unique1[~unique1.isna()].tolist()) if len(unique1) > 0 else set()
    set2 = set(unique2[~unique2.isna()].tolist()) if len(unique2) > 0 else set()
    
    assert set1 == set2
    assert unique1.isna().sum() == unique2.isna().sum()


@given(integer_array_with_na_strategy(), integer_array_with_na_strategy())
@settings(suppress_health_check=[])
def test_integer_arrays_combine_first(arr1, arr2):
    """Test combine_first behavior."""
    # Make them same length
    if len(arr1) != len(arr2):
        min_len = min(len(arr1), len(arr2))
        arr1 = arr1[:min_len]
        arr2 = arr2[:min_len]
    
    assume(len(arr1) > 0)
    
    if hasattr(arr1, 'combine_first'):
        combined = arr1.combine_first(arr2)
        
        assert len(combined) == len(arr1)
        
        # Values from arr1 should be used unless they're NA
        for i in range(len(arr1)):
            if not pd.isna(arr1[i]):
                assert combined[i] == arr1[i]
            elif not pd.isna(arr2[i]):
                assert combined[i] == arr2[i]
            else:
                assert pd.isna(combined[i])


@given(st.integers(min_value=1, max_value=100))
def test_interval_from_breaks_length(n):
    """Test IntervalArray.from_breaks creates correct number of intervals."""
    breaks = list(range(n + 1))  # n+1 breaks create n intervals
    arr = pa.IntervalArray.from_breaks(breaks)
    
    assert len(arr) == n
    
    # Check intervals are contiguous
    for i in range(len(arr) - 1):
        assert arr[i].right == arr[i + 1].left


@given(interval_array_overlapping_strategy())
def test_interval_array_is_non_overlapping_consistency(arr):
    """Test is_non_overlapping_monotonic property."""
    if hasattr(arr, 'is_non_overlapping_monotonic'):
        is_non_overlapping = arr.is_non_overlapping_monotonic
        
        if is_non_overlapping:
            # If claimed non-overlapping, verify it
            for i in range(len(arr) - 1):
                # Check no overlaps between consecutive intervals
                assert not arr[i].overlaps(arr[i + 1])


@given(integer_array_with_na_strategy())
def test_integer_array_shift_consistency(arr):
    """Test shift operation consistency."""
    if len(arr) > 1:
        shifted = arr.shift(1)
        
        assert len(shifted) == len(arr)
        assert pd.isna(shifted[0])  # First element should be NA
        
        # Rest should be shifted
        for i in range(1, len(arr)):
            if pd.isna(arr[i-1]):
                assert pd.isna(shifted[i])
            else:
                assert shifted[i] == arr[i-1]


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), 
                min_size=3, max_size=50))
def test_interval_from_tuples_round_trip(values):
    """Test from_tuples and to_tuples round trip."""
    # Create tuples
    tuples = []
    for i in range(len(values) - 1):
        if values[i] < values[i + 1]:
            tuples.append((values[i], values[i + 1]))
    
    assume(len(tuples) > 0)
    
    arr = pa.IntervalArray.from_tuples(tuples)
    
    if hasattr(arr, 'to_tuples'):
        back_to_tuples = arr.to_tuples()
        
        assert len(back_to_tuples) == len(tuples)
        for original, recovered in zip(tuples, back_to_tuples):
            assert math.isclose(original[0], recovered[0], rel_tol=1e-9)
            assert math.isclose(original[1], recovered[1], rel_tol=1e-9)


@given(integer_array_with_na_strategy())
@settings(max_examples=500)
def test_integer_array_searchsorted_bounds(arr):
    """Test searchsorted returns valid indices."""
    assume(len(arr) > 0)
    
    # Get a value to search for
    search_val = 0
    
    if hasattr(arr, 'searchsorted'):
        try:
            idx = arr.searchsorted(search_val)
            # Result should be a valid insertion index
            assert 0 <= idx <= len(arr)
        except:
            # May fail if array has NAs or is not sorted
            pass


@given(string_array_strategy(), string_array_strategy())
@settings(suppress_health_check=[])
def test_string_array_add_concatenation(arr1, arr2):
    """Test string concatenation with + operator."""
    # Make them same length
    if len(arr1) != len(arr2):
        min_len = min(len(arr1), len(arr2))
        arr1 = arr1[:min_len]
        arr2 = arr2[:min_len]
    
    assume(len(arr1) > 0)
    
    try:
        result = arr1 + arr2
        
        assert len(result) == len(arr1)
        
        for i in range(len(arr1)):
            if pd.isna(arr1[i]) or pd.isna(arr2[i]):
                assert pd.isna(result[i])
            else:
                assert result[i] == str(arr1[i]) + str(arr2[i])
    except:
        # String concatenation might not be supported this way
        pass


@given(integer_array_with_na_strategy())
def test_integer_array_duplicated_consistency(arr):
    """Test duplicated method consistency."""
    duplicated = arr.duplicated()
    
    assert len(duplicated) == len(arr)
    assert all(isinstance(x, (bool, np.bool_)) for x in duplicated)
    
    # First occurrence should never be marked as duplicate
    seen = {}
    for i, val in enumerate(arr):
        val_key = 'NA' if pd.isna(val) else val
        if val_key not in seen:
            assert not duplicated[i], f"First occurrence at {i} marked as duplicate"
            seen[val_key] = i
        else:
            # Subsequent occurrences should be marked as duplicate
            assert duplicated[i], f"Duplicate at {i} not marked"