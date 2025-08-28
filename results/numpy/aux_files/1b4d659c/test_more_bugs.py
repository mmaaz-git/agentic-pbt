import numpy as np
import numpy.random
from hypothesis import given, strategies as st, assume, settings
import math
import pytest

@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100)
)
def test_multivariate_normal_dimension_consistency(n, m, k):
    """Multivariate normal should enforce dimension consistency"""
    mean = np.zeros(n)
    cov = np.eye(m)
    
    if n != m:
        with pytest.raises(ValueError):
            numpy.random.multivariate_normal(mean, cov)
    else:
        result = numpy.random.multivariate_normal(mean, cov, size=k)
        assert result.shape == (k, n)

@given(st.integers(min_value=2, max_value=10))
def test_multivariate_normal_non_psd_covariance(n):
    """Multivariate normal should check for positive semi-definite covariance"""
    mean = np.zeros(n)
    cov = -np.eye(n)
    
    with pytest.raises(ValueError):
        numpy.random.multivariate_normal(mean, cov, check_valid='raise')

@given(st.floats(min_value=0.01, max_value=100))
def test_zipf_parameter_constraint(a):
    """Zipf distribution requires a > 1"""
    if a <= 1:
        with pytest.raises(ValueError):
            numpy.random.zipf(a)
    else:
        result = numpy.random.zipf(a, size=10)
        assert all(r >= 1 for r in result)

@given(st.floats())
def test_logseries_parameter_constraint(p):
    """Logseries requires 0 < p < 1"""
    if 0 < p < 1:
        result = numpy.random.logseries(p, size=10)
        assert all(r >= 1 for r in result)
    else:
        with pytest.raises(ValueError):
            numpy.random.logseries(p)

@given(
    st.floats(min_value=0.1, max_value=100),
    st.floats(min_value=0.1, max_value=100)
)
def test_f_distribution_positive(dfnum, dfden):
    """F-distribution should produce positive values"""
    result = numpy.random.f(dfnum, dfden, size=100)
    assert all(r >= 0 for r in result)

@given(st.floats())
def test_chisquare_df_constraint(df):
    """Chi-square requires df > 0"""
    if df <= 0:
        with pytest.raises(ValueError):
            numpy.random.chisquare(df)
    else:
        result = numpy.random.chisquare(df, size=10)
        assert all(r >= 0 for r in result)

@given(
    st.integers(min_value=1, max_value=100),
    st.floats(min_value=0.01, max_value=0.99)
)
def test_negative_binomial_parameter_types(n, p):
    """Negative binomial parameters should be validated"""
    result = numpy.random.negative_binomial(n, p, size=10)
    assert all(r >= 0 for r in result)

@given(st.floats())
def test_wald_mean_constraint(mean):
    """Wald distribution requires mean > 0"""
    scale = 1.0
    if mean <= 0:
        with pytest.raises(ValueError):
            numpy.random.wald(mean, scale)
    else:
        result = numpy.random.wald(mean, scale, size=10)
        assert all(r > 0 for r in result)

@given(st.floats())
def test_weibull_a_constraint(a):
    """Weibull requires a > 0"""
    if a <= 0:
        with pytest.raises(ValueError):
            numpy.random.weibull(a)
    else:
        result = numpy.random.weibull(a, size=10)
        assert all(r >= 0 for r in result)

@given(
    st.floats(min_value=-100, max_value=100),
    st.floats(min_value=-100, max_value=100),
    st.floats(min_value=-100, max_value=100)
)
def test_triangular_ordering(left, mode, right):
    """Triangular distribution requires left <= mode <= right"""
    if left <= mode <= right:
        result = numpy.random.triangular(left, mode, right, size=10)
        assert all(left <= r <= right for r in result)
    else:
        with pytest.raises(ValueError):
            numpy.random.triangular(left, mode, right)

@given(st.integers(min_value=0, max_value=2**32))
def test_random_integers_deprecated(high):
    """random_integers is deprecated but still works"""
    if high == 0:
        return
    
    with pytest.deprecated_call():
        result = numpy.random.random_integers(1, high)
        assert 1 <= result <= high

@given(st.floats(min_value=0.01, max_value=100))
def test_standard_t_df(df):
    """Standard t distribution with df parameter"""
    result = numpy.random.standard_t(df, size=100)
    assert len(result) == 100

@given(
    st.floats(min_value=0.1, max_value=100),
    st.floats()
)
def test_noncentral_chisquare_parameters(df, nonc):
    """Noncentral chi-square parameter validation"""
    if nonc < 0:
        with pytest.raises(ValueError):
            numpy.random.noncentral_chisquare(df, nonc)
    else:
        result = numpy.random.noncentral_chisquare(df, nonc, size=10)
        assert all(r >= 0 for r in result)

@given(
    st.floats(min_value=-100, max_value=100),
    st.floats(min_value=0.01, max_value=100)
)
def test_logistic_parameters(loc, scale):
    """Logistic distribution parameter validation"""
    result = numpy.random.logistic(loc, scale, size=100)
    assert len(result) == 100

@given(
    st.floats(),
    st.floats()
)
def test_lognormal_parameters(mean, sigma):
    """Lognormal requires sigma > 0"""
    if sigma <= 0:
        with pytest.raises(ValueError):
            numpy.random.lognormal(mean, sigma)
    else:
        result = numpy.random.lognormal(mean, sigma, size=10)
        assert all(r > 0 for r in result)

@given(st.floats(min_value=0.01, max_value=100))
def test_standard_gamma_shape(shape):
    """Standard gamma distribution"""
    result = numpy.random.standard_gamma(shape, size=100)
    assert all(r >= 0 for r in result)

@given(st.floats())
def test_power_a_constraint(a):
    """Power distribution requires a > 0"""
    if a <= 0:
        with pytest.raises(ValueError):
            numpy.random.power(a)
    else:
        result = numpy.random.power(a, size=10)
        assert all(0 <= r <= 1 for r in result)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])