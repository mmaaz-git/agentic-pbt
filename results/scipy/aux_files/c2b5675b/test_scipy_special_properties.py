import numpy as np
import scipy.special as sp
from hypothesis import given, assume, strategies as st, settings
import math


# Strategy for valid probabilities (0 < p < 1)
probabilities = st.floats(min_value=1e-10, max_value=1-1e-10)

# Strategy for positive real parameters
positive_params = st.floats(min_value=0.1, max_value=100)

# Strategy for safe floats (avoiding inf/nan)
safe_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)


@given(probabilities)
def test_expit_logit_round_trip(p):
    """Test that expit and logit are inverses: expit(logit(p)) = p for 0 < p < 1"""
    result = sp.expit(sp.logit(p))
    assert math.isclose(result, p, rel_tol=1e-9, abs_tol=1e-12)


@given(safe_floats)
def test_logit_expit_round_trip(x):
    """Test that logit and expit are inverses: logit(expit(x)) = x for all x"""
    result = sp.logit(sp.expit(x))
    assert math.isclose(result, x, rel_tol=1e-9, abs_tol=1e-12)


@given(positive_params, positive_params, probabilities)
def test_betainc_betaincinv_round_trip(a, b, x):
    """Test that betainc and betaincinv are inverses"""
    y = sp.betainc(a, b, x)
    x_recovered = sp.betaincinv(a, b, y)
    assert math.isclose(x_recovered, x, rel_tol=1e-7, abs_tol=1e-10)


@given(positive_params, positive_params, probabilities)
def test_betaincinv_betainc_round_trip(a, b, y):
    """Test inverse in other direction: betainc(a, b, betaincinv(a, b, y)) = y"""
    x = sp.betaincinv(a, b, y)
    y_recovered = sp.betainc(a, b, x)
    assert math.isclose(y_recovered, y, rel_tol=1e-7, abs_tol=1e-10)


@given(st.lists(safe_floats, min_size=1, max_size=10))
def test_logsumexp_correctness(x):
    """Test that exp(logsumexp(x)) = sum(exp(x))"""
    x_array = np.array(x)
    lse = sp.logsumexp(x_array)
    expected = np.sum(np.exp(x_array))
    actual = np.exp(lse)
    # Use relative tolerance for large values, absolute for small
    assert np.isclose(actual, expected, rtol=1e-10, atol=1e-12)


@given(st.lists(safe_floats, min_size=2, max_size=10))
def test_logsumexp_with_scaling(x):
    """Test logsumexp with scaling factor b"""
    x_array = np.array(x)
    # Test with b = ones (should be same as no scaling)
    b = np.ones_like(x_array)
    lse_with_b = sp.logsumexp(x_array, b=b)
    lse_without_b = sp.logsumexp(x_array)
    assert np.isclose(lse_with_b, lse_without_b, rtol=1e-10, atol=1e-12)


@given(st.floats(min_value=-0.999, max_value=0.999))
def test_erf_erfinv_round_trip(y):
    """Test that erf and erfinv are inverses for valid erf outputs (-1 < y < 1)"""
    x = sp.erfinv(y)
    y_recovered = sp.erf(x)
    assert math.isclose(y_recovered, y, rel_tol=1e-9, abs_tol=1e-12)


@given(safe_floats)
def test_erfinv_erf_round_trip(x):
    """Test inverse in other direction: erfinv(erf(x)) = x"""
    y = sp.erf(x)
    x_recovered = sp.erfinv(y)
    assert math.isclose(x_recovered, x, rel_tol=1e-9, abs_tol=1e-12)


@given(st.floats(min_value=1e-10, max_value=1-1e-10))
def test_erfc_erfcinv_round_trip(y):
    """Test that erfc and erfcinv are inverses for valid erfc outputs (0 < y < 2)"""
    # erfc outputs are in (0, 2), but erfcinv expects (0, 2)
    # For round-trip, we use (0, 1) to be safe
    x = sp.erfcinv(y)
    y_recovered = sp.erfc(x)
    assert math.isclose(y_recovered, y, rel_tol=1e-9, abs_tol=1e-12)


@given(positive_params, probabilities)
def test_gammainc_gammaincinv_round_trip(a, y):
    """Test that gammainc and gammaincinv are inverses"""
    x = sp.gammaincinv(a, y)
    y_recovered = sp.gammainc(a, x)
    assert math.isclose(y_recovered, y, rel_tol=1e-7, abs_tol=1e-10)


@given(positive_params, st.floats(min_value=0.1, max_value=50))
def test_gammaincinv_gammainc_round_trip(a, x):
    """Test inverse in other direction: gammaincinv(a, gammainc(a, x)) = x"""
    y = sp.gammainc(a, x)
    assume(0 < y < 1)  # Skip edge cases
    x_recovered = sp.gammaincinv(a, y)
    assert math.isclose(x_recovered, x, rel_tol=1e-7, abs_tol=1e-10)


@given(positive_params, probabilities)
def test_gammaincc_gammainccinv_round_trip(a, y):
    """Test that gammaincc and gammainccinv are inverses"""
    x = sp.gammainccinv(a, y)
    y_recovered = sp.gammaincc(a, x)
    assert math.isclose(y_recovered, y, rel_tol=1e-7, abs_tol=1e-10)


# Test for edge case behaviors documented in the functions
@given(st.floats(min_value=-1e10, max_value=-1e-10))
def test_logit_negative_input(x):
    """Test that logit returns nan for negative inputs as documented"""
    result = sp.logit(x)
    assert np.isnan(result)


@given(st.floats(min_value=1.0 + 1e-10, max_value=1e10))
def test_logit_greater_than_one(x):
    """Test that logit returns nan for inputs > 1 as documented"""
    result = sp.logit(x)
    assert np.isnan(result)


def test_logit_edge_cases():
    """Test documented edge cases for logit"""
    assert sp.logit(0) == -np.inf
    assert sp.logit(1) == np.inf