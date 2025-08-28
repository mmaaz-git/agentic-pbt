import numpy as np
import scipy.stats as ss
from hypothesis import given, assume, strategies as st, settings
import math
import pytest


# Strategy for generating reasonable floating point arrays
float_array_strategy = st.lists(
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=100
).map(np.array)

positive_float_array_strategy = st.lists(
    st.floats(min_value=1e-10, max_value=1e6, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=100
).map(np.array)


@given(float_array_strategy)
def test_rankdata_preserves_length(arr):
    """rankdata should preserve the length of the input array"""
    ranks = ss.rankdata(arr)
    assert len(ranks) == len(arr)


@given(float_array_strategy)
def test_rankdata_range_invariant(arr):
    """rankdata should produce ranks between 1 and n (inclusive)"""
    ranks = ss.rankdata(arr)
    n = len(arr)
    assert np.all(ranks >= 1)
    assert np.all(ranks <= n)


@given(float_array_strategy, st.sampled_from(['average', 'min', 'max', 'dense', 'ordinal']))
def test_rankdata_ordinal_produces_permutation(arr, method):
    """rankdata with ordinal method should produce a permutation of 1..n"""
    if method == 'ordinal':
        ranks = ss.rankdata(arr, method=method)
        n = len(arr)
        # For ordinal, ranks should be a permutation of 1..n
        assert set(ranks) == set(range(1, n + 1))


@given(float_array_strategy)
def test_rankdata_preserves_order(arr):
    """rankdata should preserve the relative order of distinct elements"""
    assume(len(arr) > 1)
    ranks = ss.rankdata(arr)
    # For any two indices where arr[i] < arr[j], we should have ranks[i] < ranks[j]
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] < arr[j]:
                assert ranks[i] < ranks[j]
            elif arr[i] > arr[j]:
                assert ranks[i] > ranks[j]


@given(float_array_strategy)
def test_zscore_properties(arr):
    """zscore should produce output with mean ~0 and std ~1"""
    assume(len(arr) > 1)
    assume(np.std(arr) > 1e-10)  # Need non-constant array
    
    z = ss.zscore(arr)
    # Mean should be close to 0
    assert abs(np.mean(z)) < 1e-10
    # Std should be close to 1
    assert abs(np.std(z, ddof=0) - 1.0) < 1e-10


@given(float_array_strategy)
def test_zscore_inverse(arr):
    """zscore should be invertible given mean and std"""
    assume(len(arr) > 1)
    assume(np.std(arr) > 1e-10)
    
    mean = np.mean(arr)
    std = np.std(arr, ddof=0)
    z = ss.zscore(arr, ddof=0)
    # Inverse: x = z * std + mean
    reconstructed = z * std + mean
    assert np.allclose(reconstructed, arr)


@given(float_array_strategy, st.floats(min_value=0, max_value=0.49))
def test_trim_mean_properties(arr, proportion):
    """trim_mean with proportion 0 should equal regular mean"""
    assume(len(arr) > 0)
    
    if proportion == 0:
        trimmed = ss.trim_mean(arr, proportion)
        regular_mean = np.mean(arr)
        assert np.allclose(trimmed, regular_mean)


@given(positive_float_array_strategy)
def test_mean_inequality_gmean_hmean(arr):
    """For positive values: harmonic mean <= geometric mean <= arithmetic mean"""
    assume(len(arr) > 0)
    assume(np.all(arr > 0))
    
    # Calculate the three means
    h_mean = ss.hmean(arr)
    g_mean = ss.gmean(arr) 
    a_mean = np.mean(arr)
    
    # The inequality should hold (with some tolerance for floating point)
    assert h_mean <= g_mean + 1e-10
    assert g_mean <= a_mean + 1e-10


@given(positive_float_array_strategy)
def test_gmean_hmean_equality_condition(arr):
    """gmean and hmean should be equal when all values are the same"""
    assume(len(arr) > 0)
    # Make all values the same
    constant_arr = np.full_like(arr, arr[0])
    
    h_mean = ss.hmean(constant_arr)
    g_mean = ss.gmean(constant_arr)
    a_mean = np.mean(constant_arr)
    
    # All means should be equal to the constant value
    assert np.allclose(h_mean, arr[0])
    assert np.allclose(g_mean, arr[0])
    assert np.allclose(a_mean, arr[0])


@given(float_array_strategy, st.floats(min_value=0.01, max_value=0.49))
def test_trim_mean_reduces_influence_of_extremes(arr, proportion):
    """trim_mean should be less affected by extreme values than regular mean"""
    assume(len(arr) > 10)  # Need enough elements to trim
    
    # Add an extreme outlier
    arr_with_outlier = np.append(arr, np.max(arr) * 1000)
    
    regular_mean = np.mean(arr)
    regular_mean_outlier = np.mean(arr_with_outlier)
    
    trimmed_mean = ss.trim_mean(arr, proportion)
    trimmed_mean_outlier = ss.trim_mean(arr_with_outlier, proportion)
    
    # The change in trimmed mean should be less than change in regular mean
    regular_change = abs(regular_mean_outlier - regular_mean)
    trimmed_change = abs(trimmed_mean_outlier - trimmed_mean)
    
    # This property should hold unless the proportion is too small
    if proportion > 1.0 / len(arr_with_outlier):
        assert trimmed_change <= regular_change + 1e-10


@given(float_array_strategy)
def test_moment_first_equals_mean(arr):
    """First moment should equal the mean when centered"""
    assume(len(arr) > 0)
    
    first_moment = ss.moment(arr, order=1)
    # First moment about the mean should be 0
    assert abs(first_moment) < 1e-10


@given(float_array_strategy)
def test_skew_symmetry(arr):
    """Skew of a symmetric distribution should be ~0"""
    assume(len(arr) > 2)
    # Create a symmetric array
    symmetric_arr = np.concatenate([arr, -arr])
    
    skewness = ss.skew(symmetric_arr)
    # Skewness should be close to 0 for symmetric distribution
    assert abs(skewness) < 1e-10


@given(float_array_strategy, st.integers(min_value=1, max_value=99))
def test_percentile_score_relationship(arr, percentile):
    """scoreatpercentile and percentileofscore should have consistent relationship"""
    assume(len(arr) > 1)
    
    score = ss.scoreatpercentile(arr, percentile)
    # The percentile of this score should be close to the original percentile
    calculated_percentile = ss.percentileofscore(arr, score)
    
    # They might not be exactly equal due to interpolation, but should be close
    assert abs(calculated_percentile - percentile) < 20  # Some tolerance needed


@given(st.lists(st.floats(min_value=0.1, max_value=100, allow_nan=False), min_size=2, max_size=50))
def test_boxcox_round_trip(data):
    """Box-Cox transformation should be invertible"""
    data_array = np.array(data)
    assume(np.all(data_array > 0))  # Box-Cox requires positive data
    
    # Transform with specific lambda
    lmbda = 0.5
    transformed = ss.boxcox(data_array, lmbda=lmbda)
    
    # Use scipy.special.inv_boxcox for the inverse
    import scipy.special
    inv_transformed = scipy.special.inv_boxcox(transformed, lmbda)
    
    assert np.allclose(data_array, inv_transformed, rtol=1e-10)


@given(float_array_strategy)
def test_iqr_properties(arr):
    """IQR should be non-negative and less than or equal to range"""
    assume(len(arr) > 0)
    
    iqr_value = ss.iqr(arr)
    assert iqr_value >= 0
    
    # IQR should be less than or equal to the full range
    full_range = np.max(arr) - np.min(arr)
    assert iqr_value <= full_range + 1e-10


@given(float_array_strategy)
def test_sem_relationship_with_std(arr):
    """Standard error should equal std/sqrt(n)"""
    assume(len(arr) > 1)
    
    sem_value = ss.sem(arr, ddof=1)
    std_value = np.std(arr, ddof=1)
    expected_sem = std_value / np.sqrt(len(arr))
    
    assert np.allclose(sem_value, expected_sem)