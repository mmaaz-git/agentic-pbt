"""Advanced property-based tests for pandas.core - looking for edge cases"""

import numpy as np
import pandas as pd
import pandas.core.algorithms as algo
import pandas.core.sorting as sorting
from hypothesis import given, strategies as st, assume, settings, example
import pytest


# Test with more complex data structures
@given(st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=100))
@settings(max_examples=1000)
def test_factorize_with_duplicates(values):
    """Test factorize behavior with many duplicates"""
    arr = np.array(values)
    
    codes1, uniques1 = algo.factorize(arr, sort=False)
    codes2, uniques2 = algo.factorize(arr, sort=True)
    
    # Both should produce the same number of unique values
    assert len(uniques1) == len(uniques2)
    
    # The number of unique values should match np.unique
    np_unique = np.unique(arr)
    assert len(uniques1) == len(np_unique)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10), min_size=2, max_size=50))
@settings(max_examples=1000)
def test_rank_monotonicity(values):
    """Test that rank preserves order relationships"""
    arr = np.array(values)
    
    # Get ranks
    ranks = algo.rank(arr)
    
    # For any two elements, if a < b, then rank(a) < rank(b)
    for i in range(len(arr)):
        for j in range(len(arr)):
            if arr[i] < arr[j]:
                assert ranks[i] < ranks[j], f"Rank monotonicity violated: {arr[i]} < {arr[j]} but rank {ranks[i]} >= {ranks[j]}"


@given(st.lists(st.integers(), min_size=1, max_size=100))
@settings(max_examples=1000)
def test_value_counts_sum(values):
    """Test that value_counts sums to the total length"""
    arr = np.array(values)
    
    counts = algo.value_counts(arr)
    
    # Sum of all counts should equal array length
    assert counts.sum() == len(arr)
    
    # All counts should be positive
    assert np.all(counts > 0)


@given(st.lists(st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
), min_size=2, max_size=50))
@settings(max_examples=1000)
def test_diff_inverse(values):
    """Test that diff is the inverse of cumsum (with appropriate handling)"""
    arr = np.array(values, dtype=float)
    
    # Compute differences
    diff_result = algo.diff(arr, n=1)
    
    # The first element should be NaN
    assert pd.isna(diff_result[0])
    
    # diff should be the difference between consecutive elements
    for i in range(1, len(arr)):
        expected = arr[i] - arr[i-1]
        if not pd.isna(expected):
            assert np.isclose(diff_result[i], expected, rtol=1e-10)


@given(st.lists(st.integers(min_value=0, max_value=1000), min_size=10, max_size=50))
@settings(max_examples=500)
def test_factorize_consistency_with_categorical(values):
    """Test that factorize is consistent when applied to categoricals"""
    arr = np.array(values)
    
    # Regular factorize
    codes1, uniques1 = algo.factorize(arr, sort=False)
    
    # Create a categorical and factorize
    cat = pd.Categorical(arr)
    codes2, uniques2 = algo.factorize(cat, sort=False)
    
    # The codes should encode the same information
    # (they might differ in actual values, but the pattern should be the same)
    # Reconstruct and compare
    recon1 = uniques1.take(codes1) if not isinstance(uniques1, pd.Index) else np.array(uniques1.take(codes1))
    recon2 = np.array([uniques2[c] for c in codes2])
    
    assert np.array_equal(recon1, arr)
    assert np.array_equal(recon2, arr)


# Test empty and single-element arrays
@given(st.just([]))
def test_factorize_empty(values):
    """Test factorize with empty array"""
    arr = np.array(values)
    codes, uniques = algo.factorize(arr)
    
    assert len(codes) == 0
    assert len(uniques) == 0


@given(st.lists(st.integers(), min_size=1, max_size=1))
def test_factorize_single(values):
    """Test factorize with single element"""
    arr = np.array(values)
    codes, uniques = algo.factorize(arr)
    
    assert len(codes) == 1
    assert codes[0] == 0
    assert len(uniques) == 1


# Test with mixed dtypes and edge cases
@given(st.lists(st.sampled_from([0, 1, -1, 100, -100, np.inf, -np.inf]), min_size=1, max_size=20))
@settings(max_examples=500)
def test_factorize_infinity(values):
    """Test factorize with infinity values"""
    arr = np.array(values, dtype=float)
    
    codes, uniques = algo.factorize(arr, use_na_sentinel=True)
    
    # Reconstruct and verify
    if isinstance(uniques, pd.Index):
        reconstructed = np.array(uniques.take(codes))
    else:
        reconstructed = uniques.take(codes)
    
    assert np.array_equal(reconstructed, arr)


# Test sorting module functions
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50))
@settings(max_examples=500)
def test_nargsort_consistency(values):
    """Test that nargsort produces valid sorting indices"""
    arr = np.array(values)
    
    # Get sorting indices
    indices = sorting.nargsort(arr)
    
    # Sorted array should be sorted
    sorted_arr = arr[indices]
    for i in range(1, len(sorted_arr)):
        assert sorted_arr[i-1] <= sorted_arr[i]


# Complex interaction test
@given(st.lists(st.integers(min_value=0, max_value=10), min_size=5, max_size=30))
@settings(max_examples=500)
def test_factorize_unique_consistency(values):
    """Test that factorize and unique are consistent"""
    arr = np.array(values)
    
    # Get unique values directly
    unique_vals = algo.unique(arr)
    
    # Get unique values through factorize
    codes, factorize_uniques = algo.factorize(arr, sort=False)
    
    # Both should have the same unique values (though potentially in different order)
    assert set(unique_vals) == set(factorize_uniques if not isinstance(factorize_uniques, pd.Index) else factorize_uniques.values)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])