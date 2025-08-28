import scipy.special as sp
import numpy as np
from hypothesis import given, strategies as st, assume
import math


# Test for overflow/underflow in exp-related functions
@given(st.floats(min_value=-1000, max_value=1000, allow_nan=False))
def test_expit_bounds(x):
    """expit should always return values in [0, 1]"""
    result = sp.expit(x)
    assert 0 <= result <= 1, f"expit({x}) = {result} not in [0, 1]"


# Test softmax with extreme values
@given(st.lists(st.floats(min_value=-100, max_value=700, allow_nan=False), min_size=2, max_size=10))
def test_softmax_sum(values):
    """softmax should always sum to 1"""
    result = sp.softmax(values)
    total = np.sum(result)
    assert math.isclose(total, 1.0, rel_tol=1e-9), f"sum(softmax({values})) = {total} != 1"


# Test log-sum-exp inequality
@given(st.lists(st.floats(min_value=-100, max_value=100, allow_nan=False), min_size=1, max_size=10))
def test_logsumexp_inequality(values):
    """logsumexp(x) >= max(x)"""
    lse = sp.logsumexp(values)
    max_val = max(values)
    assert lse >= max_val - 1e-10, f"logsumexp({values}) = {lse} < max = {max_val}"


# Test rel_entr (relative entropy) with edge cases
@given(st.floats(min_value=0, max_value=100), st.floats(min_value=0, max_value=100))
def test_rel_entr_special_cases(x, y):
    """Test relative entropy special cases"""
    result = sp.rel_entr(x, y)
    
    # rel_entr(0, 0) should be 0
    if x == 0 and y == 0:
        assert result == 0, f"rel_entr(0, 0) = {result}, expected 0"
    
    # rel_entr(x, 0) for x > 0 should be inf
    if x > 0 and y == 0:
        assert np.isinf(result), f"rel_entr({x}, 0) = {result}, expected inf"
    
    # Result should always be non-negative or 0
    if not np.isinf(result):
        assert result >= -1e-10, f"rel_entr({x}, {y}) = {result} < 0"


# Test entr (entropy) properties
@given(st.floats(min_value=0, max_value=1000))
def test_entr_properties(x):
    """Test entropy function properties"""
    result = sp.entr(x)
    
    # entr(0) should be 0
    if x == 0:
        assert result == 0, f"entr(0) = {result}, expected 0"
    
    # entr(1) should be 0  
    if x == 1:
        assert abs(result) < 1e-10, f"entr(1) = {result}, expected 0"
    
    # For x > 0, entr(x) = -x*log(x), which is positive for 0 < x < 1
    if 0 < x < 1:
        assert result > 0, f"entr({x}) = {result} should be positive for 0 < x < 1"
    
    # For x > 1, entr(x) should be negative
    if x > 1:
        assert result < 0, f"entr({x}) = {result} should be negative for x > 1"