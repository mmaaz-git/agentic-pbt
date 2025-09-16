"""Test internal pandas.core functions for edge cases and bugs"""

import numpy as np
import pandas as pd
from pandas.core.algorithms import (
    factorize, unique, duplicated, rank, 
    diff, value_counts, safe_sort
)
from pandas.core.sorting import (
    nargsort, get_group_index
)
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test safe_sort function with edge cases
@given(st.lists(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(min_size=1, max_size=5),
), min_size=1, max_size=30))
@settings(max_examples=500)
def test_safe_sort_preserves_nan(values):
    """Test that safe_sort handles NaN values correctly"""
    arr = np.array(values)
    
    try:
        sorted_arr = safe_sort(arr)
        
        # Count NaNs in original and sorted
        orig_nan_count = pd.isna(arr).sum()
        sorted_nan_count = pd.isna(sorted_arr).sum()
        
        # NaN count should be preserved
        assert orig_nan_count == sorted_nan_count
        
        # Non-NaN values should be sorted
        if not pd.isna(sorted_arr).all():
            non_nan_sorted = sorted_arr[~pd.isna(sorted_arr)]
            # Check if sorted (for comparable types)
            try:
                for i in range(1, len(non_nan_sorted)):
                    assert non_nan_sorted[i-1] <= non_nan_sorted[i]
            except (TypeError, ValueError):
                pass  # Mixed types may not be comparable
    except (TypeError, ValueError):
        # Some arrays can't be sorted (e.g., mixed types)
        pass


# Test get_group_index_sorter
@given(st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=30))
@settings(max_examples=500)
def test_group_index_sorter(values):
    """Test get_group_index_sorter function"""
    from pandas.core.sorting import get_group_index_sorter
    
    arr = np.array(values)
    
    # Factorize the array
    codes, uniques = factorize(arr, sort=False)
    
    # Get sorter
    n_unique = len(uniques)
    sorter = get_group_index_sorter(codes, n_unique)
    
    # sorter should have same length as codes
    assert len(sorter) == len(codes)


# Test get_group_index with multiple keys
@given(
    st.lists(st.integers(min_value=0, max_value=5), min_size=5, max_size=20),
    st.lists(st.integers(min_value=0, max_value=5), min_size=5, max_size=20)
)
@settings(max_examples=500)
def test_get_group_index(values1, values2):
    """Test get_group_index for grouping operations"""
    # Ensure same length
    min_len = min(len(values1), len(values2))
    arr1 = np.array(values1[:min_len])
    arr2 = np.array(values2[:min_len])
    
    # Get group index
    labels = [arr1, arr2]
    shape = [arr1.max() + 1, arr2.max() + 1]
    
    group_idx = get_group_index(labels, shape, sort=True, xnull=False)
    
    # Group index should have same length as input
    assert len(group_idx) == len(arr1)
    
    # All group indices should be non-negative
    assert np.all(group_idx >= 0)


# Test rank with different methods
@given(st.lists(st.floats(allow_nan=True, allow_infinity=False, min_value=-100, max_value=100), min_size=2, max_size=30))
@settings(max_examples=500)
def test_rank_methods_consistency(values):
    """Test that different ranking methods are consistent"""
    arr = np.array(values)
    
    # Skip if all NaN
    if pd.isna(arr).all():
        return
    
    # Test different methods
    methods = ['average', 'min', 'max', 'first', 'dense']
    ranks = {}
    
    for method in methods:
        try:
            ranks[method] = rank(arr, method=method)
        except Exception:
            pass
    
    # All methods should produce same shape
    for method in ranks:
        assert ranks[method].shape == arr.shape
        
    # For non-NaN values, all ranks should be >= 1
    for method in ranks:
        non_nan_ranks = ranks[method][~pd.isna(arr)]
        if len(non_nan_ranks) > 0:
            assert np.all(non_nan_ranks >= 1)


# Test edge case: factorize with all same values
@given(st.integers(), st.integers(min_value=1, max_value=100))
def test_factorize_all_same(value, size):
    """Test factorize when all values are the same"""
    arr = np.full(size, value)
    
    codes, uniques = factorize(arr)
    
    # Should have exactly one unique value
    assert len(uniques) == 1
    assert uniques[0] == value
    
    # All codes should be 0
    assert np.all(codes == 0)


# Test with datetime-like data
@given(st.lists(st.integers(min_value=0, max_value=1_000_000_000), min_size=1, max_size=30))
@settings(max_examples=500)
def test_factorize_with_timestamps(values):
    """Test factorize with timestamp-like integers"""
    arr = np.array(values, dtype='int64')
    
    codes, uniques = factorize(arr)
    
    # Verify round-trip
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    assert np.array_equal(reconstructed, arr)


# Test potential overflow scenarios
@given(st.lists(st.sampled_from([
    np.iinfo(np.int64).max,
    np.iinfo(np.int64).min,
    np.iinfo(np.int32).max,
    np.iinfo(np.int32).min,
    0, 1, -1
]), min_size=1, max_size=20))
@settings(max_examples=300)
def test_factorize_overflow_boundaries(values):
    """Test factorize with values at integer boundaries"""
    arr = np.array(values, dtype='int64')
    
    codes, uniques = factorize(arr)
    
    # Verify round-trip without overflow
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    assert np.array_equal(reconstructed, arr)


# Test duplicated with edge cases
@given(st.lists(st.one_of(
    st.just(np.nan),
    st.just(None),
    st.just(pd.NaT),
    st.floats(allow_nan=True),
), min_size=2, max_size=20))
@settings(max_examples=500)
def test_duplicated_with_na_values(values):
    """Test duplicated with various NA representations"""
    arr = np.array(values, dtype=object)
    
    # Test all keep modes
    for keep in ['first', 'last', False]:
        dup = duplicated(arr, keep=keep)
        
        # Result should be boolean array of same length
        assert dup.dtype == bool
        assert len(dup) == len(arr)


# Complex test: factorize preserves information content
@given(st.lists(st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.text(min_size=1, max_size=3),
    st.floats(allow_nan=False, allow_infinity=False),
), min_size=5, max_size=50))
@settings(max_examples=500)
def test_factorize_information_preservation(values):
    """Test that factorize preserves all information about the data"""
    arr = np.array(values)
    
    # Factorize
    codes, uniques = factorize(arr, sort=False)
    
    # Create mapping from original to codes
    value_to_code = {}
    for i, val in enumerate(arr):
        if codes[i] not in value_to_code:
            value_to_code[codes[i]] = []
        value_to_code[codes[i]].append(i)
    
    # Each code should map to exactly one unique value
    for code in value_to_code:
        if code >= 0:  # Skip -1 (NaN sentinel)
            indices = value_to_code[code]
            vals = [arr[i] for i in indices]
            # All values for a given code should be equal
            for v in vals[1:]:
                if not pd.isna(vals[0]) and not pd.isna(v):
                    assert v == vals[0] or (isinstance(v, float) and isinstance(vals[0], float) and np.isclose(v, vals[0]))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])