import math
import numpy as np
import scipy.special as sp
import scipy.stats as stats
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test 1: expit/logit round-trip property
@given(st.floats(min_value=-100, max_value=100, allow_nan=False))
def test_expit_logit_round_trip_from_x(x):
    """Test that logit(expit(x)) = x for reasonable x values"""
    y = sp.expit(x)
    x_recovered = sp.logit(y)
    assert math.isclose(x_recovered, x, rel_tol=1e-9, abs_tol=1e-10)


@given(st.floats(min_value=1e-10, max_value=1-1e-10))
def test_logit_expit_round_trip_from_p(p):
    """Test that expit(logit(p)) = p for p in (0,1)"""
    x = sp.logit(p)
    p_recovered = sp.expit(x)
    assert math.isclose(p_recovered, p, rel_tol=1e-9, abs_tol=1e-10)


# Test 2: erf/erfinv round-trip property
@given(st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_erf_erfinv_round_trip_from_x(x):
    """Test that erfinv(erf(x)) = x"""
    y = sp.erf(x)
    x_recovered = sp.erfinv(y)
    assert math.isclose(x_recovered, x, rel_tol=1e-9, abs_tol=1e-10)


@given(st.floats(min_value=-0.9999999, max_value=0.9999999))
def test_erfinv_erf_round_trip_from_y(y):
    """Test that erf(erfinv(y)) = y for y in (-1,1)"""
    x = sp.erfinv(y)
    y_recovered = sp.erf(x)
    assert math.isclose(y_recovered, y, rel_tol=1e-9, abs_tol=1e-10)


# Test 3: erfc/erfcinv round-trip property
@given(st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_erfc_erfcinv_round_trip_from_x(x):
    """Test that erfcinv(erfc(x)) = x"""
    y = sp.erfc(x)
    x_recovered = sp.erfcinv(y)
    assert math.isclose(x_recovered, x, rel_tol=1e-9, abs_tol=1e-10)


@given(st.floats(min_value=1e-10, max_value=2-1e-10))
def test_erfcinv_erfc_round_trip_from_y(y):
    """Test that erfc(erfcinv(y)) = y for y in (0,2)"""
    x = sp.erfcinv(y)
    y_recovered = sp.erfc(x)
    assert math.isclose(y_recovered, y, rel_tol=1e-9, abs_tol=1e-10)


# Test 4: erfc(x) = 1 - erf(x) property
@given(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
def test_erfc_equals_one_minus_erf(x):
    """Test that erfc(x) = 1 - erf(x) as stated in docstring"""
    erfc_val = sp.erfc(x)
    erf_val = sp.erf(x)
    expected = 1.0 - erf_val
    assert math.isclose(erfc_val, expected, rel_tol=1e-9, abs_tol=1e-10)


# Test 5: norm.cdf/norm.ppf round-trip property
@given(st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_norm_cdf_ppf_round_trip_from_x(x):
    """Test that norm.ppf(norm.cdf(x)) = x"""
    p = stats.norm.cdf(x)
    x_recovered = stats.norm.ppf(p)
    assert math.isclose(x_recovered, x, rel_tol=1e-9, abs_tol=1e-10)


@given(st.floats(min_value=1e-10, max_value=1-1e-10))
def test_norm_ppf_cdf_round_trip_from_p(p):
    """Test that norm.cdf(norm.ppf(p)) = p for p in (0,1)"""
    x = stats.norm.ppf(p)
    p_recovered = stats.norm.cdf(x)
    assert math.isclose(p_recovered, p, rel_tol=1e-9, abs_tol=1e-10)


# Test with arrays for vectorized functions
@given(st.lists(st.floats(min_value=1e-10, max_value=1-1e-10), min_size=1, max_size=100))
def test_expit_logit_array_round_trip(p_list):
    """Test expit/logit round-trip with arrays"""
    p_array = np.array(p_list)
    x_array = sp.logit(p_array)
    p_recovered = sp.expit(x_array)
    assert np.allclose(p_recovered, p_array, rtol=1e-9, atol=1e-10)


# Test edge cases and special values
@given(st.floats(min_value=-1e308, max_value=1e308, allow_nan=False))
def test_expit_logit_extended_range(x):
    """Test expit/logit with extended range including very large values"""
    y = sp.expit(x)
    # y should be in (0,1)
    assert 0 <= y <= 1
    
    # For very large |x|, y will be very close to 0 or 1
    # Only test round-trip for moderate values
    if abs(x) < 30:  # sigmoid saturates around ±30
        x_recovered = sp.logit(y)
        assert math.isclose(x_recovered, x, rel_tol=1e-7, abs_tol=1e-8)