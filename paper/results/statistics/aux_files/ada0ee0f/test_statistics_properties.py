import math
import statistics
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import assume, given, settings, strategies as st


# Strategy for positive floats
positive_floats = st.floats(min_value=1e-100, max_value=1e100, allow_nan=False, allow_infinity=False)

# Strategy for reasonable floats
reasonable_floats = st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)

# Strategy for non-empty lists
nonempty_lists = lambda strat: st.lists(strat, min_size=1, max_size=100)


# Property 1: Arithmetic mean >= Geometric mean >= Harmonic mean for positive numbers
@given(nonempty_lists(positive_floats))
def test_mean_inequality(data):
    """Test the AM-GM-HM inequality for positive numbers."""
    try:
        am = statistics.mean(data)
        gm = statistics.geometric_mean(data)
        hm = statistics.harmonic_mean(data)
        
        # The inequality: AM >= GM >= HM
        assert hm <= gm or math.isclose(hm, gm, rel_tol=1e-9)
        assert gm <= am or math.isclose(gm, am, rel_tol=1e-9)
    except (OverflowError, ValueError):
        # Some extreme values might cause overflow
        pass


# Property 2: Median is invariant under monotonic transformations that preserve order
@given(nonempty_lists(reasonable_floats))
def test_median_order_preservation(data):
    """Test that median preserves relative position under order-preserving transformations."""
    median1 = statistics.median(data)
    
    # Apply order-preserving transformation: f(x) = 2x + 3
    transformed = [2 * x + 3 for x in data]
    median2 = statistics.median(transformed)
    
    # The median should transform the same way
    expected = 2 * median1 + 3
    assert math.isclose(median2, expected, rel_tol=1e-9)


# Property 3: Variance is scale-invariant: Var(c*X) = c^2 * Var(X)
@given(
    nonempty_lists(reasonable_floats),
    st.floats(min_value=0.1, max_value=10, allow_nan=False)
)
def test_variance_scaling(data, scale):
    """Test that variance scales quadratically."""
    if len(data) < 2:
        return  # Variance needs at least 2 points
    
    var1 = statistics.variance(data)
    scaled_data = [x * scale for x in data]
    var2 = statistics.variance(scaled_data)
    
    expected = var1 * (scale ** 2)
    assert math.isclose(var2, expected, rel_tol=1e-9) or (var1 == 0 and var2 == 0)


# Property 4: Standard deviation is the square root of variance
@given(nonempty_lists(reasonable_floats))
def test_stdev_variance_relationship(data):
    """Test that stdev = sqrt(variance)."""
    if len(data) < 2:
        return
    
    var = statistics.variance(data)
    stdev = statistics.stdev(data)
    
    assert math.isclose(stdev ** 2, var, rel_tol=1e-9)


# Property 5: Quantiles should preserve order and bounds
@given(
    nonempty_lists(reasonable_floats),
    st.integers(min_value=2, max_value=10)
)
def test_quantiles_properties(data, n):
    """Test that quantiles are ordered and within data bounds."""
    quantiles = statistics.quantiles(data, n=n)
    
    # Quantiles should be in non-decreasing order
    for i in range(len(quantiles) - 1):
        assert quantiles[i] <= quantiles[i + 1] or math.isclose(quantiles[i], quantiles[i + 1])
    
    # All quantiles should be within the data range
    data_min, data_max = min(data), max(data)
    for q in quantiles:
        assert data_min <= q <= data_max or math.isclose(q, data_min) or math.isclose(q, data_max)


# Property 6: Correlation coefficient bounds: -1 <= r <= 1
@given(
    nonempty_lists(reasonable_floats),
    nonempty_lists(reasonable_floats)
)
def test_correlation_bounds(x, y):
    """Test that correlation coefficient is between -1 and 1."""
    # Make them the same length
    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]
    
    if len(x) < 2:
        return
    
    try:
        corr = statistics.correlation(x, y)
        assert -1.0 <= corr <= 1.0 or math.isclose(abs(corr), 1.0, abs_tol=1e-9)
    except statistics.StatisticsError:
        # Can happen if all values are the same
        pass


# Property 7: Linear regression slope matches correlation * (sy/sx)
@given(
    nonempty_lists(reasonable_floats),
    nonempty_lists(reasonable_floats)
)
def test_linear_regression_correlation_relationship(x, y):
    """Test relationship between linear regression slope and correlation."""
    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]
    
    if len(x) < 2:
        return
    
    try:
        # Get correlation and regression
        corr = statistics.correlation(x, y)
        regression = statistics.linear_regression(x, y)
        
        # Calculate standard deviations
        sx = statistics.stdev(x)
        sy = statistics.stdev(y)
        
        if sx > 0:
            # The slope should equal correlation * (sy/sx)
            expected_slope = corr * (sy / sx)
            assert math.isclose(regression.slope, expected_slope, rel_tol=1e-9)
    except (statistics.StatisticsError, ZeroDivisionError):
        pass


# Property 8: Mode is always an element of the input data
@given(nonempty_lists(st.integers(min_value=-100, max_value=100)))
def test_mode_in_data(data):
    """Test that mode returns an element from the input data."""
    mode_val = statistics.mode(data)
    assert mode_val in data


# Property 9: Multimode returns all most frequent values
@given(nonempty_lists(st.integers(min_value=-10, max_value=10)))
def test_multimode_properties(data):
    """Test that multimode returns all values with maximum frequency."""
    modes = statistics.multimode(data)
    
    # All modes should be in the data
    for mode in modes:
        assert mode in data
    
    # Count frequencies
    from collections import Counter
    counts = Counter(data)
    if counts:
        max_count = max(counts.values())
        
        # All returned modes should have the maximum frequency
        for mode in modes:
            assert counts[mode] == max_count
        
        # All values with maximum frequency should be in modes
        for value, count in counts.items():
            if count == max_count:
                assert value in modes


# Property 10: KDE integration approximately equals 1
@given(
    nonempty_lists(reasonable_floats),
    st.floats(min_value=0.01, max_value=10.0)
)
@settings(max_examples=50)  # KDE is computationally expensive
def test_kde_integration(data, bandwidth):
    """Test that KDE integrates to approximately 1."""
    try:
        kde_func = statistics.kde(data, h=bandwidth)
        
        # Find reasonable integration bounds
        data_min, data_max = min(data), max(data)
        data_range = data_max - data_min
        lower = data_min - 5 * bandwidth
        upper = data_max + 5 * bandwidth
        
        # Numerical integration
        n_points = 1000
        step = (upper - lower) / n_points
        integral = sum(kde_func(lower + i * step) * step for i in range(n_points))
        
        # Should integrate to approximately 1
        assert 0.9 <= integral <= 1.1
    except (OverflowError, ValueError, statistics.StatisticsError):
        pass


# Property 11: median_low and median_high are actual data points
@given(nonempty_lists(reasonable_floats))
def test_median_low_high_in_data(data):
    """Test that median_low and median_high return actual data points."""
    med_low = statistics.median_low(data)
    med_high = statistics.median_high(data)
    
    assert med_low in data
    assert med_high in data
    
    # median_low <= median <= median_high
    med = statistics.median(data)
    assert med_low <= med <= med_high or math.isclose(med_low, med) or math.isclose(med, med_high)


# Property 12: Test covariance symmetry: cov(X,Y) = cov(Y,X)
@given(
    nonempty_lists(reasonable_floats),
    nonempty_lists(reasonable_floats)
)
def test_covariance_symmetry(x, y):
    """Test that covariance is symmetric."""
    min_len = min(len(x), len(y))
    x, y = x[:min_len], y[:min_len]
    
    if len(x) < 2:
        return
    
    cov_xy = statistics.covariance(x, y)
    cov_yx = statistics.covariance(y, x)
    
    assert math.isclose(cov_xy, cov_yx, rel_tol=1e-9)


# Property 13: fmean with equal weights equals regular fmean
@given(nonempty_lists(reasonable_floats))
def test_fmean_equal_weights(data):
    """Test that fmean with equal weights gives same result as without weights."""
    mean1 = statistics.fmean(data)
    
    # Create equal weights
    weights = [1.0] * len(data)
    mean2 = statistics.fmean(data, weights=weights)
    
    assert math.isclose(mean1, mean2, rel_tol=1e-9)


# Property 14: Test rank function produces valid rankings
@given(nonempty_lists(reasonable_floats))
def test_rank_properties(data):
    """Test that rank function produces valid rankings."""
    ranks = statistics.rank(data)
    
    # Ranks should be between 1 and n
    n = len(data)
    for rank in ranks:
        assert 1 <= rank <= n
    
    # Average of ranks should be (n+1)/2
    avg_rank = sum(ranks) / n
    expected_avg = (n + 1) / 2
    assert math.isclose(avg_rank, expected_avg, rel_tol=1e-9)


# Property 15: pvariance <= variance (population variance <= sample variance)
@given(nonempty_lists(reasonable_floats))
def test_population_sample_variance_relationship(data):
    """Test that population variance <= sample variance for n > 1."""
    if len(data) < 2:
        return
    
    pvar = statistics.pvariance(data)
    var = statistics.variance(data)
    
    # For n > 1, sample variance >= population variance
    # They're related by factor (n-1)/n
    assert pvar <= var or math.isclose(pvar, var, rel_tol=1e-9)
    
    # Check the exact relationship
    n = len(data)
    expected_pvar = var * (n - 1) / n
    assert math.isclose(pvar, expected_pvar, rel_tol=1e-9)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])