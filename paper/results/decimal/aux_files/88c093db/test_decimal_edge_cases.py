import decimal
import math
from hypothesis import given, strategies as st, assume, settings, example


@given(st.text(alphabet='0123456789+-eE.', min_size=1, max_size=50))
def test_decimal_string_parsing_consistency(s):
    """Test that Decimal string parsing is consistent with its output"""
    try:
        d = decimal.Decimal(s)
        # If parsing succeeds, converting back to string and re-parsing should give same value
        s2 = str(d)
        d2 = decimal.Decimal(s2)
        assert d == d2
    except (decimal.InvalidOperation, ValueError):
        # Invalid strings should consistently fail
        pass


@given(st.integers(), st.integers(1, 100))
def test_power_modulo_consistency(base, exp):
    """Test that power with modulo behaves consistently"""
    assume(exp > 0)
    
    d_base = decimal.Decimal(base)
    d_exp = decimal.Decimal(exp)
    modulo = decimal.Decimal('1000000')
    
    # Test __pow__ with three arguments (base, exp, modulo)
    if modulo != 0:
        result1 = pow(d_base, d_exp, modulo)
        result2 = (d_base ** d_exp) % modulo
        
        # These should be equivalent for reasonable values
        if result1.is_finite() and result2.is_finite():
            # Allow for precision differences
            diff = abs(result1 - result2)
            assert diff < decimal.Decimal('1')


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_decimal_float_precision(f):
    """Test precision preservation in float->Decimal->float conversion"""
    d = decimal.Decimal.from_float(f)
    f2 = float(d)
    
    # For representable floats, conversion should be exact
    if abs(f) < 1e308 and abs(f) > 1e-308:
        if f == 0:
            assert f2 == 0
        else:
            # Check relative error
            rel_error = abs(f - f2) / abs(f)
            assert rel_error < 1e-15


@given(st.integers(-1000, 1000), st.integers(-10, 10))
def test_scaleb_boundaries(mantissa, scale):
    """Test scaleb with various scales"""
    d = decimal.Decimal(mantissa)
    scale_d = decimal.Decimal(scale)
    
    result = d.scaleb(scale_d)
    
    if result.is_finite():
        # Verify the scaling
        expected = d * (decimal.Decimal(10) ** scale)
        assert result == expected


@given(st.integers(-100, 100))
def test_logical_operations_on_integers(n):
    """Test logical operations work correctly on integer decimals"""
    d = decimal.Decimal(n)
    
    # Logical operations should work on non-negative integers
    if n >= 0:
        # XOR with itself should be 0
        xor_self = d.logical_xor(d)
        assert xor_self == decimal.Decimal(0)
        
        # AND with itself should be itself
        and_self = d.logical_and(d)
        assert and_self == d
        
        # OR with itself should be itself
        or_self = d.logical_or(d)
        assert or_self == d


@given(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False))
def test_ln_exp_precision(x):
    """Test that ln and exp maintain precision for reasonable values"""
    assume(x > 0)
    
    d = decimal.Decimal(str(x))
    
    # Save original precision
    ctx = decimal.getcontext()
    original_prec = ctx.prec
    
    try:
        # Use high precision for this test
        ctx.prec = 50
        
        ln_d = d.ln()
        exp_ln_d = ln_d.exp()
        
        # Check round-trip
        if exp_ln_d.is_finite():
            rel_error = abs(exp_ln_d - d) / d if d != 0 else abs(exp_ln_d)
            assert rel_error < decimal.Decimal('1e-40')
    finally:
        ctx.prec = original_prec


@given(st.integers(-1000000, 1000000))
def test_to_integral_exact_flag(n):
    """Test to_integral_exact sets inexact flag correctly"""
    # Create a decimal that's already integral
    d = decimal.Decimal(n)
    
    ctx = decimal.getcontext()
    ctx.clear_flags()
    
    result = d.to_integral_exact()
    
    # Since input is already integral, should not set Inexact flag
    assert not ctx.flags[decimal.Inexact]
    assert result == d
    
    # Now test with non-integral
    ctx.clear_flags()
    d2 = decimal.Decimal(n) + decimal.Decimal('0.5')
    result2 = d2.to_integral_exact()
    
    # This should set the Inexact flag
    assert ctx.flags[decimal.Inexact]


@given(st.integers(0, 1000000))
def test_sqrt_perfect_squares(n):
    """Test sqrt on perfect squares gives exact results"""
    d = decimal.Decimal(n * n)
    
    sqrt_d = d.sqrt()
    
    # For perfect squares, result should be exact
    assert sqrt_d * sqrt_d == d
    assert sqrt_d == decimal.Decimal(n)


@given(st.sampled_from(['+', '-']), st.text(alphabet='0123456789', min_size=1, max_size=100))
def test_sign_preservation(sign, digits):
    """Test that sign is preserved correctly"""
    s = sign + digits
    d = decimal.Decimal(s)
    
    if sign == '-' and not all(c == '0' for c in digits):
        assert d < 0
        assert d.is_signed()
    else:
        assert d >= 0
        assert not d.is_signed() or d == 0


@given(st.integers(1, 1000))
def test_division_by_power_of_ten(n):
    """Test division by powers of 10 is exact"""
    d = decimal.Decimal(n)
    divisor = decimal.Decimal('10')
    
    result = d / divisor
    
    # Verify exactness by multiplying back
    back = result * divisor
    assert back == d


@given(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False))
def test_log10_properties(x):
    """Test log10 properties"""
    d = decimal.Decimal(str(x))
    
    log10_d = d.log10()
    
    if log10_d.is_finite():
        # 10^log10(x) should equal x
        power = decimal.Decimal(10) ** log10_d
        
        if power.is_finite():
            rel_error = abs(power - d) / d
            assert rel_error < decimal.Decimal('1e-20')


@given(st.integers(-100, 100), st.integers(-100, 100))
def test_remainder_vs_modulo(a, b):
    """Test relationship between remainder and modulo"""
    assume(b != 0)
    
    da = decimal.Decimal(a)
    db = decimal.Decimal(b)
    
    remainder = da % db
    
    # Verify fundamental property: a = quotient * b + remainder
    quotient = (da - remainder) / db
    assert da == quotient * db + remainder
    
    # Check sign rules for remainder
    if b > 0:
        assert 0 <= remainder < db
    else:
        assert db < remainder <= 0


@given(st.integers(0, 1000))
def test_shift_operations(n):
    """Test shift operations maintain value relationships"""
    d = decimal.Decimal(n)
    
    # Shift left by 1 should multiply by 10
    shifted_left = d.shift(1)
    assert shifted_left == d * 10
    
    # Shift right by 1 should divide by 10 (integer division)
    shifted_right = d.shift(-1)
    assert shifted_right == d // 10


@given(st.sampled_from(['0', '-0', '+0', '0.0', '-0.0', '+0.0', '0e0', '-0e0']))
def test_zero_representations(zero_str):
    """Test different representations of zero"""
    d = decimal.Decimal(zero_str)
    
    assert d == 0
    assert d.is_zero()
    
    # Check sign of zero
    if zero_str.startswith('-'):
        assert d.is_signed()
    else:
        assert not d.is_signed()


@given(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False))
def test_asin_acos_domain(x):
    """Test inverse trig functions respect domain"""
    # These functions are not in standard decimal module
    # This is just to verify if they were added
    d = decimal.Decimal(str(x))
    
    # Check if decimal has trig functions (it doesn't in standard Python)
    if hasattr(d, 'asin'):
        asin_result = d.asin()
        assert -math.pi/2 <= float(asin_result) <= math.pi/2
    
    if hasattr(d, 'acos'):
        acos_result = d.acos()
        assert 0 <= float(acos_result) <= math.pi


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])