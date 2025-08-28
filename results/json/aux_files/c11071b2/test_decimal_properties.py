import decimal
import math
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite


@composite
def valid_decimal_strings(draw):
    sign = draw(st.sampled_from(['', '-', '+']))
    
    choice = draw(st.integers(0, 3))
    
    if choice == 0:
        integer_part = draw(st.text(alphabet='0123456789', min_size=1, max_size=10))
        decimal_part = draw(st.text(alphabet='0123456789', min_size=0, max_size=10))
        if decimal_part:
            number = f"{integer_part}.{decimal_part}"
        else:
            number = integer_part
    elif choice == 1:
        mantissa = draw(st.text(alphabet='0123456789', min_size=1, max_size=5))
        exponent = draw(st.integers(-100, 100))
        number = f"{mantissa}e{exponent}"
    elif choice == 2:
        integer_part = draw(st.text(alphabet='0123456789', min_size=1, max_size=5))
        decimal_part = draw(st.text(alphabet='0123456789', min_size=0, max_size=5))
        exponent = draw(st.integers(-50, 50))
        if decimal_part:
            number = f"{integer_part}.{decimal_part}e{exponent}"
        else:
            number = f"{integer_part}e{exponent}"
    else:
        number = draw(st.sampled_from(['0', '0.0', '1', '10', '100']))
    
    return sign + number


@composite  
def finite_decimals(draw):
    source = draw(st.one_of(
        valid_decimal_strings(),
        st.integers(-10**10, 10**10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100)
    ))
    return decimal.Decimal(str(source))


@given(valid_decimal_strings())
def test_string_round_trip(s):
    d = decimal.Decimal(s)
    reconstructed = decimal.Decimal(str(d))
    assert d == reconstructed


@given(finite_decimals())
def test_tuple_round_trip(d):
    assume(d.is_finite())
    tuple_repr = d.as_tuple()
    reconstructed = decimal.Decimal(tuple_repr)
    assert d == reconstructed


@given(finite_decimals())
def test_addition_identity(d):
    zero = decimal.Decimal('0')
    assert d + zero == d
    assert zero + d == d


@given(finite_decimals())
def test_multiplication_identity(d):
    one = decimal.Decimal('1')
    assert d * one == d
    assert one * d == d


@given(finite_decimals())
def test_multiplication_by_zero(d):
    zero = decimal.Decimal('0')
    result = d * zero
    assert result == zero or result.is_nan()


@given(finite_decimals(), finite_decimals())
def test_addition_commutative(a, b):
    assert a + b == b + a


@given(finite_decimals(), finite_decimals())
def test_multiplication_commutative(a, b):
    assert a * b == b * a


@given(finite_decimals(), finite_decimals(), finite_decimals())
def test_addition_associative(a, b, c):
    ctx = decimal.getcontext()
    original_prec = ctx.prec
    ctx.prec = 100
    
    try:
        left = (a + b) + c
        right = a + (b + c)
        
        if left.is_finite() and right.is_finite():
            assert left == right
    finally:
        ctx.prec = original_prec


@given(finite_decimals())
def test_negate_twice(d):
    assert d.copy_negate().copy_negate() == d


@given(finite_decimals())
def test_abs_idempotent(d):
    assert d.copy_abs().copy_abs() == d.copy_abs()


@given(finite_decimals())
def test_sqrt_squared(d):
    assume(d >= 0)
    assume(d.is_finite())
    
    sqrt_d = d.sqrt()
    if sqrt_d.is_finite():
        squared = sqrt_d * sqrt_d
        
        if d == 0:
            assert squared == 0
        else:
            original_str = str(d)
            squared_str = str(squared)
            
            if '.' in original_str:
                sig_digits = len(original_str.replace('.', '').lstrip('0').rstrip('0'))
            else:
                sig_digits = len(original_str.lstrip('0'))
            
            if sig_digits > 0:
                ratio = squared / d if d != 0 else decimal.Decimal('1')
                assert abs(ratio - decimal.Decimal('1')) < decimal.Decimal('1e-10')


@given(finite_decimals(), finite_decimals())
def test_comparison_consistency(a, b):
    if a < b:
        assert not (a >= b)
        assert not (a > b)
        assert a <= b
        assert a != b
    
    if a > b:
        assert not (a <= b)
        assert not (a < b)
        assert a >= b
        assert a != b
    
    if a == b:
        assert a <= b
        assert a >= b
        assert not (a < b)
        assert not (a > b)


@given(finite_decimals())
def test_division_by_self(d):
    assume(d != 0)
    assume(d.is_finite())
    result = d / d
    assert result == decimal.Decimal('1')


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_from_float_to_float(f):
    d = decimal.Decimal.from_float(f)
    
    if d.is_finite():
        reconstructed = float(d)
        
        if abs(f) < 1e-100 or abs(f) > 1e100:
            pass
        else:
            assert math.isclose(f, reconstructed, rel_tol=1e-10)


@given(finite_decimals())
def test_quantize_identity(d):
    assume(d.is_finite())
    
    exp = d.as_tuple().exponent
    if exp >= 0:
        quantum = decimal.Decimal('1')
    else:
        quantum = decimal.Decimal(10) ** exp
    
    quantized = d.quantize(quantum)
    assert quantized == d


@given(finite_decimals(), finite_decimals())
def test_min_max_consistency(a, b):
    min_val = min(a, b)
    max_val = max(a, b)
    
    assert min_val <= max_val
    assert min_val == a or min_val == b
    assert max_val == a or max_val == b
    
    if a < b:
        assert min_val == a and max_val == b
    elif a > b:
        assert min_val == b and max_val == a
    else:
        assert min_val == max_val == a == b


@given(finite_decimals())
def test_ln_exp_inverse(d):
    assume(d > 0)
    assume(d.is_finite())
    assume(d < decimal.Decimal('1e100'))
    
    ln_d = d.ln()
    if ln_d.is_finite():
        exp_ln_d = ln_d.exp()
        if exp_ln_d.is_finite():
            ratio = exp_ln_d / d
            assert abs(ratio - decimal.Decimal('1')) < decimal.Decimal('1e-10')


@given(finite_decimals())
def test_copy_sign_consistency(d):
    pos = decimal.Decimal('1')
    neg = decimal.Decimal('-1')
    
    pos_signed = d.copy_sign(pos)
    neg_signed = d.copy_sign(neg)
    
    if d == 0:
        pass
    else:
        assert pos_signed.copy_abs() == d.copy_abs()
        assert neg_signed.copy_abs() == d.copy_abs()
        
        if not d.is_zero():
            assert pos_signed >= 0
            assert neg_signed <= 0


@given(st.integers(-1000000, 1000000))
def test_integer_decimal_conversion(i):
    d = decimal.Decimal(i)
    assert int(d) == i


@given(finite_decimals(), finite_decimals(), finite_decimals())
def test_fma_vs_manual(a, b, c):
    assume(all(x.is_finite() for x in [a, b, c]))
    
    ctx = decimal.getcontext()
    original_prec = ctx.prec
    
    try:
        ctx.prec = 50
        
        fma_result = a.fma(b, c)
        
        manual_result = (a * b) + c
        
        if fma_result.is_finite() and manual_result.is_finite():
            diff = abs(fma_result - manual_result)
            max_val = max(abs(fma_result), abs(manual_result), decimal.Decimal('1'))
            relative_diff = diff / max_val
            
            assert relative_diff < decimal.Decimal('1e-20')
    finally:
        ctx.prec = original_prec


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])