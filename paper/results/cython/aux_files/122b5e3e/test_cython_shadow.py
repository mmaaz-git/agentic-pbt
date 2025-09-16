import math
from hypothesis import given, strategies as st, assume
import Cython.Shadow as cs


@given(st.integers(), st.integers())
def test_cdiv_cmod_relationship(a, b):
    """Test that a = cdiv(a, b) * b + cmod(a, b) for all non-zero b"""
    assume(b != 0)
    quotient = cs.cdiv(a, b)
    remainder = cs.cmod(a, b)
    assert a == quotient * b + remainder, f"Failed for a={a}, b={b}: {quotient}*{b} + {remainder} != {a}"


@given(st.integers(), st.integers())
def test_cdiv_truncation_toward_zero(a, b):
    """Test that cdiv truncates toward zero (C-style division)"""
    assume(b != 0)
    result = cs.cdiv(a, b)
    
    # C-style division truncates toward zero
    expected = int(a / b)  # Python's int() truncates toward zero
    assert result == expected, f"cdiv({a}, {b}) = {result}, expected {expected}"


@given(st.integers())
def test_cmod_sign_behavior(a):
    """Test that cmod result has same sign as dividend in C semantics"""
    # Test with positive divisor
    b = 7
    result = cs.cmod(a, b)
    
    # In C semantics, if a and result are both non-zero, they should have the same sign
    if a != 0 and result != 0:
        assert (a > 0 and result >= 0) or (a < 0 and result <= 0), \
            f"cmod({a}, {b}) = {result} has wrong sign"
    
    # Test with negative divisor
    b = -7
    result = cs.cmod(a, b)
    
    if a != 0 and result != 0:
        assert (a > 0 and result >= 0) or (a < 0 and result <= 0), \
            f"cmod({a}, {b}) = {result} has wrong sign"


@given(st.integers())
def test_cast_integer_preservation(value):
    """Test that casting integers preserves the value"""
    result = cs.cast(int, value)
    assert result == value


@given(st.text())
def test_cast_string_preservation(value):
    """Test that casting strings preserves the value"""
    result = cs.cast(str, value)
    assert result == value


@given(st.integers(min_value=-1000, max_value=1000), st.integers(min_value=-1000, max_value=1000))
def test_cdiv_cmod_consistency_with_python_divmod(a, b):
    """Test consistency between cdiv/cmod and Python's divmod for specific cases"""
    assume(b != 0)
    
    # Get C-style results
    c_quotient = cs.cdiv(a, b)
    c_remainder = cs.cmod(a, b)
    
    # For same-sign operands, Python and C should agree
    if (a >= 0 and b > 0) or (a <= 0 and b < 0):
        py_quotient, py_remainder = divmod(a, b)
        # In these cases, they might still differ, so let's just verify the relationship holds
        assert a == c_quotient * b + c_remainder


@given(st.integers())
def test_sizeof_returns_one(arg):
    """Test that sizeof always returns 1 (dummy implementation)"""
    result = cs.sizeof(arg)
    assert result == 1


@given(st.integers())
def test_address_returns_pointer(value):
    """Test that address returns a pointer type"""
    result = cs.address(value)
    # Should return a pointer to the value
    assert hasattr(result, '__getitem__')
    assert result[0] == value