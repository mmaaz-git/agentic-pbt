import scipy.special as sp
import scipy.stats as stats
import numpy as np
from hypothesis import given, strategies as st


# Bug 1: expit/logit round-trip fails catastrophically for large x
@given(st.floats(min_value=30, max_value=100))
def test_expit_logit_catastrophic_failure(x):
    """Test that logit(expit(x)) should return x, not inf"""
    y = sp.expit(x)
    x_recovered = sp.logit(y)
    # This should not be infinite!
    assert np.isfinite(x_recovered), f"logit(expit({x})) returned {x_recovered}, expected finite value near {x}"
    

# Bug 2: erf/erfinv round-trip fails catastrophically for large x  
@given(st.floats(min_value=5.5, max_value=10))
def test_erf_erfinv_catastrophic_failure(x):
    """Test that erfinv(erf(x)) should return x, not inf"""
    y = sp.erf(x)
    x_recovered = sp.erfinv(y)
    # This should not be infinite!
    assert np.isfinite(x_recovered), f"erfinv(erf({x})) returned {x_recovered}, expected finite value near {x}"


# Bug 3: erfc/erfcinv round-trip fails catastrophically for large negative x
@given(st.floats(min_value=-10, max_value=-5.5))
def test_erfc_erfcinv_catastrophic_failure(x):
    """Test that erfcinv(erfc(x)) should return x, not inf"""
    y = sp.erfc(x)
    x_recovered = sp.erfcinv(y)
    # This should not be infinite!
    assert np.isfinite(x_recovered), f"erfcinv(erfc({x})) returned {x_recovered}, expected finite value near {x}"


# Bug 4: norm.cdf/ppf round-trip fails for extreme values
@given(st.floats(min_value=8, max_value=10))
def test_norm_cdf_ppf_catastrophic_failure(x):
    """Test that norm.ppf(norm.cdf(x)) should return x, not inf"""
    p = stats.norm.cdf(x)
    x_recovered = stats.norm.ppf(p)
    # This should not be infinite!
    assert np.isfinite(x_recovered), f"norm.ppf(norm.cdf({x})) returned {x_recovered}, expected finite value near {x}"