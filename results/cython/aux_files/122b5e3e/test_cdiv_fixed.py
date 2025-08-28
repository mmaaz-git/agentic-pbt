import Cython.Shadow as cs
from hypothesis import given, strategies as st, assume


def c_style_div_expected(a, b):
    """What C-style division should return - truncates toward zero"""
    if b == 0:
        raise ZeroDivisionError
    # C truncates toward zero, not floor
    if (a < 0) != (b < 0):  # Different signs
        return -(-a // b if a < 0 else a // -b)
    else:  # Same signs
        return abs(a) // abs(b)


@given(st.integers(min_value=-10000, max_value=10000), 
       st.integers(min_value=-10000, max_value=10000))
def test_cdiv_c_semantics(a, b):
    """Test that cdiv correctly implements C-style truncating division"""
    assume(b != 0)
    result = cs.cdiv(a, b)
    expected = c_style_div_expected(a, b)
    assert result == expected, f"cdiv({a}, {b}) = {result}, expected {expected}"


@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=-10000, max_value=10000))
def test_cdiv_cmod_identity(a, b):
    """Test the fundamental identity: a = cdiv(a,b) * b + cmod(a,b)"""
    assume(b != 0)
    q = cs.cdiv(a, b)
    r = cs.cmod(a, b)
    assert a == q * b + r, f"Identity failed: {a} != {q}*{b} + {r}"


@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=-10000, max_value=10000))
def test_cmod_range(a, b):
    """Test that |cmod(a,b)| < |b| and has correct sign"""
    assume(b != 0)
    r = cs.cmod(a, b)
    
    # Remainder should be smaller than divisor in absolute value
    assert abs(r) < abs(b), f"|cmod({a}, {b})| = {abs(r)} >= {abs(b)}"
    
    # In C semantics, remainder has same sign as dividend (or is zero)
    if r != 0:
        assert (a > 0 and r > 0) or (a < 0 and r < 0), \
            f"cmod({a}, {b}) = {r} has wrong sign (a={'positive' if a > 0 else 'negative'})"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])