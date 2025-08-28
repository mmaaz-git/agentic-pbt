"""Focused tests to find real bugs in pandas.core"""

import numpy as np
import pandas as pd
from pandas.core.algorithms import factorize, unique, duplicated, rank
from pandas.core.sorting import nargsort, get_group_index
from hypothesis import given, strategies as st, assume, settings, example
import pytest
import warnings


# Test factorize with object arrays containing None and NaN
@given(st.lists(st.one_of(
    st.none(),
    st.just(float('nan')),
    st.integers(),
    st.text(min_size=1, max_size=3),
), min_size=1, max_size=20))
@settings(max_examples=1000)
def test_factorize_none_vs_nan(values):
    """Test factorize distinguishes between None and NaN in object arrays"""
    arr = np.array(values, dtype=object)
    
    codes, uniques = factorize(arr, use_na_sentinel=False)
    
    # Count None and NaN in original
    none_count = sum(1 for v in values if v is None)
    nan_count = sum(1 for v in values if isinstance(v, float) and pd.isna(v))
    
    # If both None and NaN are present, they should be treated as different
    if none_count > 0 and nan_count > 0:
        # Check if uniques contains both
        unique_none_count = sum(1 for v in uniques if v is None)
        unique_nan_count = sum(1 for v in uniques if isinstance(v, float) and pd.isna(v))
        
        # Both should appear in uniques when use_na_sentinel=False
        assert unique_none_count > 0, "None should be in uniques"
        assert unique_nan_count > 0, "NaN should be in uniques"


# Test rank with all NaN values
@given(st.integers(min_value=1, max_value=20))
@settings(max_examples=100)
def test_rank_all_nan(size):
    """Test rank behavior with all NaN values"""
    arr = np.full(size, np.nan, dtype=float)
    
    # Test different methods
    for method in ['average', 'min', 'max', 'first', 'dense']:
        ranks = rank(arr, method=method)
        
        # All ranks should be NaN for NaN inputs
        assert pd.isna(ranks).all(), f"rank method={method} should return NaN for all NaN input"


# Test factorize with very large arrays to check for integer overflow
@given(st.integers(min_value=100, max_value=1000))
@settings(max_examples=10)
def test_factorize_large_unique_values(n_unique):
    """Test factorize with many unique values"""
    # Create array with n_unique unique values
    arr = np.arange(n_unique)
    np.random.shuffle(arr)
    
    codes, uniques = factorize(arr)
    
    # Should have exactly n_unique unique values
    assert len(uniques) == n_unique
    
    # Codes should be valid indices
    assert codes.min() >= 0
    assert codes.max() < n_unique
    
    # Verify round-trip
    reconstructed = uniques.take(codes)
    assert np.array_equal(reconstructed, arr)


# Test duplicated with mixed types
@given(st.lists(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(min_size=1, max_size=2),
    st.booleans(),
), min_size=2, max_size=20))
@settings(max_examples=500)
def test_duplicated_mixed_types(values):
    """Test duplicated with mixed type arrays"""
    arr = np.array(values, dtype=object)
    
    # Test that duplicated works with mixed types
    dup_first = duplicated(arr, keep='first')
    dup_last = duplicated(arr, keep='last')
    dup_false = duplicated(arr, keep=False)
    
    # Basic consistency checks
    assert len(dup_first) == len(arr)
    assert len(dup_last) == len(arr)
    assert len(dup_false) == len(arr)
    
    # If an element appears only once, it shouldn't be marked as duplicate
    unique_vals = unique(arr)
    for val in unique_vals:
        indices = [i for i, v in enumerate(arr) if v == val or (pd.isna(v) and pd.isna(val))]
        if len(indices) == 1:
            idx = indices[0]
            assert not dup_false[idx]


# Test edge case: factorize with -1 values when use_na_sentinel=True
@given(st.lists(st.integers(min_value=-5, max_value=5), min_size=1, max_size=30))
@settings(max_examples=500)
def test_factorize_negative_one_confusion(values):
    """Test factorize doesn't confuse -1 values with NA sentinel"""
    arr = np.array(values)
    
    codes, uniques = factorize(arr, use_na_sentinel=True)
    
    # If -1 is in the original array, it should be in uniques
    if -1 in arr:
        assert -1 in uniques or -1 in uniques.values if isinstance(uniques, pd.Index) else False
    
    # Verify round-trip works correctly even with -1 values
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    assert np.array_equal(reconstructed, arr)


# Test get_group_index with edge cases
@given(st.data())
@settings(max_examples=500)
def test_get_group_index_edge_cases(data):
    """Test get_group_index with various edge cases"""
    
    # Generate random dimensions
    n = data.draw(st.integers(min_value=1, max_value=20))
    n_keys = data.draw(st.integers(min_value=1, max_value=3))
    
    # Generate labels
    labels = []
    shape = []
    for _ in range(n_keys):
        max_val = data.draw(st.integers(min_value=1, max_value=10))
        label = data.draw(st.lists(st.integers(min_value=0, max_value=max_val-1), min_size=n, max_size=n))
        labels.append(np.array(label))
        shape.append(max_val)
    
    # Test with sort=True and sort=False
    for sort in [True, False]:
        group_idx = get_group_index(labels, shape, sort=sort, xnull=False)
        
        # Basic properties
        assert len(group_idx) == n
        assert group_idx.dtype == np.int64
        
        # All indices should be valid
        max_possible = np.prod(shape, dtype=np.int64)
        assert np.all(group_idx >= 0)
        assert np.all(group_idx < max_possible)


# Test factorize with string arrays containing empty strings
@given(st.lists(st.one_of(
    st.text(min_size=0, max_size=5),
    st.just(""),
), min_size=1, max_size=30))
@settings(max_examples=500)
def test_factorize_empty_strings(values):
    """Test factorize handles empty strings correctly"""
    arr = np.array(values, dtype=object)
    
    codes, uniques = factorize(arr)
    
    # Empty string should be treated as a valid value
    empty_count = values.count("")
    if empty_count > 0:
        assert "" in uniques or "" in uniques.values if isinstance(uniques, pd.Index) else False
    
    # Verify round-trip
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    assert np.array_equal(reconstructed, arr)


# Test nargsort with NaN values
@given(st.lists(st.floats(allow_nan=True, allow_infinity=False), min_size=1, max_size=30))
@settings(max_examples=500)
def test_nargsort_nan_handling(values):
    """Test nargsort handles NaN correctly"""
    arr = np.array(values)
    
    # Get sorting indices
    indices = nargsort(arr)
    
    # Sorted array
    sorted_arr = arr[indices]
    
    # NaNs should be at the end
    nan_mask = pd.isna(sorted_arr)
    if nan_mask.any():
        first_nan_idx = np.where(nan_mask)[0][0]
        # All elements after first NaN should also be NaN
        assert pd.isna(sorted_arr[first_nan_idx:]).all()
        
        # Non-NaN part should be sorted
        if first_nan_idx > 0:
            non_nan_part = sorted_arr[:first_nan_idx]
            for i in range(1, len(non_nan_part)):
                assert non_nan_part[i-1] <= non_nan_part[i]


# Test factorize with bytes objects
@given(st.lists(st.binary(min_size=0, max_size=5), min_size=1, max_size=20))
@settings(max_examples=500)
def test_factorize_bytes(values):
    """Test factorize with bytes objects"""
    arr = np.array(values, dtype=object)
    
    codes, uniques = factorize(arr)
    
    # Verify round-trip
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    # Check element-wise equality for bytes
    assert len(reconstructed) == len(arr)
    for i in range(len(arr)):
        assert reconstructed[i] == arr[i]


# Test rank with infinity values
@given(st.lists(st.sampled_from([float('inf'), float('-inf'), 0.0, 1.0, -1.0]), min_size=2, max_size=20))
@settings(max_examples=500)
def test_rank_infinity(values):
    """Test rank handles infinity correctly"""
    arr = np.array(values)
    
    ranks = rank(arr)
    
    # -inf should have lowest rank, inf should have highest
    if float('-inf') in arr and float('inf') in arr:
        neg_inf_indices = np.where(arr == float('-inf'))[0]
        pos_inf_indices = np.where(arr == float('inf'))[0]
        
        # All -inf ranks should be less than all inf ranks
        for neg_idx in neg_inf_indices:
            for pos_idx in pos_inf_indices:
                assert ranks[neg_idx] < ranks[pos_idx]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])