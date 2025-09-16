"""Property-based tests for pandas.core.algorithms"""

import numpy as np
import pandas as pd
import pandas.core.algorithms as algo
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategy for generating various array-like inputs
array_strategy = st.one_of(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50),
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=1, max_size=50),
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=30),
    st.lists(st.booleans(), min_size=1, max_size=50),
)


@given(array_strategy)
@settings(max_examples=1000)
def test_factorize_round_trip(values):
    """Test that factorize creates codes that can reconstruct original values"""
    arr = np.array(values)
    
    # Test without sorting
    codes, uniques = algo.factorize(arr, sort=False)
    
    # Round-trip property: uniques[codes] should equal original values
    if isinstance(uniques, pd.Index):
        reconstructed = uniques.take(codes)
        reconstructed = np.array(reconstructed)
    else:
        reconstructed = uniques.take(codes)
    
    # Check equality (handling potential dtype differences)
    if arr.dtype == object or np.issubdtype(arr.dtype, np.str_):
        assert np.array_equal(reconstructed, arr)
    else:
        assert np.allclose(reconstructed, arr, rtol=1e-10)


@given(array_strategy)
@settings(max_examples=1000)
def test_factorize_sorted_uniques(values):
    """Test that factorize with sort=True produces sorted uniques"""
    arr = np.array(values)
    
    # Skip if values aren't sortable
    try:
        np.sort(arr)
    except (TypeError, ValueError):
        assume(False)
    
    codes, uniques = algo.factorize(arr, sort=True)
    
    # Convert to array for consistent comparison
    if isinstance(uniques, pd.Index):
        uniques_arr = np.array(uniques)
    else:
        uniques_arr = uniques
    
    # Check if uniques are sorted
    sorted_uniques = np.sort(uniques_arr)
    assert np.array_equal(uniques_arr, sorted_uniques)


@given(array_strategy)
@settings(max_examples=1000)
def test_unique_duplicated_invariant(values):
    """Test that unique values are not marked as duplicated"""
    arr = np.array(values)
    
    # Get unique values
    unique_vals = algo.unique(arr)
    
    # Check duplicated on unique values
    dup_mask = algo.duplicated(unique_vals, keep=False)
    
    # No unique values should be marked as duplicated
    assert not np.any(dup_mask)


@given(array_strategy)
@settings(max_examples=1000)
def test_duplicated_first_last_consistency(values):
    """Test consistency between keep='first' and keep='last' in duplicated"""
    arr = np.array(values)
    
    dup_first = algo.duplicated(arr, keep='first')
    dup_last = algo.duplicated(arr, keep='last')
    dup_all = algo.duplicated(arr, keep=False)
    
    # Elements marked as duplicated with keep=False should include
    # all elements marked with keep='first' or keep='last'
    assert np.all(dup_first[dup_first] <= dup_all[dup_first])
    assert np.all(dup_last[dup_last] <= dup_all[dup_last])
    
    # If an element appears only once, it shouldn't be marked as duplicated in any mode
    unique_vals = algo.unique(arr)
    for val in unique_vals:
        indices = np.where(arr == val)[0]
        if len(indices) == 1:
            idx = indices[0]
            assert not dup_first[idx]
            assert not dup_last[idx]
            assert not dup_all[idx]


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=2, max_size=50))
@settings(max_examples=1000)
def test_factorize_code_bounds(values):
    """Test that factorize codes are within valid bounds"""
    arr = np.array(values)
    
    codes, uniques = algo.factorize(arr, use_na_sentinel=True)
    
    # Codes should be between -1 (for NaN) and len(uniques)-1
    assert np.all(codes >= -1)
    assert np.all(codes < len(uniques))
    
    # Non-negative codes should be valid indices into uniques
    valid_codes = codes[codes >= 0]
    if len(valid_codes) > 0:
        assert np.all(valid_codes < len(uniques))


@given(st.lists(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    st.floats(allow_nan=True, allow_infinity=False),
), min_size=1, max_size=50))
@settings(max_examples=1000)
def test_factorize_nan_handling(values):
    """Test that factorize handles NaN values correctly"""
    arr = np.array(values)
    
    # Test with use_na_sentinel=True (default)
    codes_with_sentinel, uniques_with_sentinel = algo.factorize(arr, use_na_sentinel=True)
    
    # NaN values should be coded as -1
    nan_mask = pd.isna(arr)
    if np.any(nan_mask):
        assert np.all(codes_with_sentinel[nan_mask] == -1)
        # uniques should not contain NaN
        assert not pd.isna(uniques_with_sentinel).any()
    
    # Test with use_na_sentinel=False
    codes_no_sentinel, uniques_no_sentinel = algo.factorize(arr, use_na_sentinel=False)
    
    # All codes should be non-negative
    assert np.all(codes_no_sentinel >= 0)
    
    # If there were NaNs, they should appear in uniques
    if np.any(nan_mask):
        if isinstance(uniques_no_sentinel, pd.Index):
            assert pd.isna(uniques_no_sentinel).any()
        else:
            assert pd.isna(uniques_no_sentinel).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])