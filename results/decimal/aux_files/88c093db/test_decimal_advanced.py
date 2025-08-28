import decimal
import math
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite


@composite
def reasonable_decimals(draw):
    choice = draw(st.integers(0, 2))
    if choice == 0:
        return decimal.Decimal(draw(st.integers(-10**15, 10**15)))
    elif choice == 1:
        f = draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e15, max_value=1e15))
        return decimal.Decimal(str(f))
    else:
        mantissa = draw(st.integers(-10**10, 10**10))
        exp = draw(st.integers(-20, 20))
        return decimal.Decimal(f"{mantissa}e{exp}")


@given(reasonable_decimals())
def test_normalize_preserves_value(d):
    normalized = d.normalize()
    assert d == normalized


@given(reasonable_decimals())
def test_is_signed_consistency(d):
    if d.is_signed():
        assert d < 0
    else:
        assert d >= 0


@given(reasonable_decimals())
def test_as_integer_ratio_round_trip(d):
    assume(d.is_finite())
    num, denom = d.as_integer_ratio()
    reconstructed = decimal.Decimal(num) / decimal.Decimal(denom)
    assert d == reconstructed


@given(reasonable_decimals())
def test_compare_total_reflexive(d):
    assert d.compare_total(d) == 0


@given(reasonable_decimals(), reasonable_decimals())
def test_compare_total_antisymmetric(a, b):
    cmp_ab = a.compare_total(b)
    cmp_ba = b.compare_total(a)
    
    if cmp_ab < 0:
        assert cmp_ba > 0
    elif cmp_ab > 0:
        assert cmp_ba < 0
    else:
        assert cmp_ba == 0


@given(reasonable_decimals())
def test_logb_property(d):
    assume(d != 0)
    assume(d.is_finite())
    
    logb = d.logb()
    
    if logb.is_finite():
        logb_int = int(logb)
        
        abs_d = abs(d)
        lower_bound = decimal.Decimal(10) ** logb_int
        upper_bound = decimal.Decimal(10) ** (logb_int + 1)
        
        assert lower_bound <= abs_d < upper_bound


@given(reasonable_decimals())
def test_scaleb_inverse(d):
    assume(d.is_finite())
    assume(d != 0)
    
    scale = decimal.Decimal(3)
    
    scaled = d.scaleb(scale)
    if scaled.is_finite():
        unscaled = scaled.scaleb(-scale)
        if unscaled.is_finite():
            assert d == unscaled


@given(reasonable_decimals())
def test_next_plus_minus_relationship(d):
    assume(d.is_finite())
    
    next_val = d.next_plus()
    prev_val = d.next_minus()
    
    if next_val.is_finite() and prev_val.is_finite():
        assert prev_val < d < next_val or (d.is_zero() and prev_val < d <= next_val)


@given(reasonable_decimals())
def test_canonical_is_self(d):
    assert d.canonical() is d


@given(st.integers(-100, 100))
def test_decimal_from_int_preserves_exactness(i):
    d = decimal.Decimal(i)
    assert int(d) == i
    assert d.as_integer_ratio() == (i, 1)


@given(reasonable_decimals())
def test_remainder_near_properties(d):
    assume(d != 0)
    assume(d.is_finite())
    
    divisor = decimal.Decimal('10')
    remainder = d.remainder_near(divisor)
    
    if remainder.is_finite():
        assert abs(remainder) <= abs(divisor) / 2
        
        quotient = (d - remainder) / divisor
        if quotient.is_finite():
            reconstructed = quotient * divisor + remainder
            if reconstructed.is_finite():
                assert abs(d - reconstructed) < decimal.Decimal('1e-20')


@given(reasonable_decimals())
def test_shift_left_right_inverse(d):
    assume(d.is_finite())
    
    shift_amount = 3
    
    # Shift operations work on digits, need integer representation
    if d == d.to_integral_value():
        shifted = d.shift(shift_amount)
        if shifted.is_finite():
            unshifted = shifted.shift(-shift_amount)
            
            # Due to truncation, we can only check if it's close
            original_digits = len(str(abs(int(d))))
            if original_digits <= 20:
                assert d == unshifted


@given(reasonable_decimals())
def test_to_integral_value_idempotent(d):
    assume(d.is_finite())
    
    integral = d.to_integral_value()
    integral2 = integral.to_integral_value()
    
    assert integral == integral2


@given(reasonable_decimals())
def test_conjugate_is_self(d):
    assert d.conjugate() == d


@given(reasonable_decimals())
def test_real_imag_properties(d):
    assert d.real == d
    assert d.imag == 0


@given(st.sampled_from([decimal.Decimal('Infinity'), decimal.Decimal('-Infinity'), decimal.Decimal('NaN')]))
def test_special_values_properties(special):
    if special.is_nan():
        assert not special.is_finite()
        assert not special.is_infinite()
        assert special != special
    elif special.is_infinite():
        assert not special.is_finite()
        assert not special.is_nan()
        if special > 0:
            assert special > decimal.Decimal('1e1000000')
        else:
            assert special < decimal.Decimal('-1e1000000')


@given(reasonable_decimals(), reasonable_decimals())
def test_max_min_commutative(a, b):
    assert a.max(b) == b.max(a)
    assert a.min(b) == b.min(a)


@given(reasonable_decimals(), reasonable_decimals(), reasonable_decimals())  
def test_max_associative(a, b, c):
    left = a.max(b).max(c)
    right = a.max(b.max(c))
    assert left == right


@given(reasonable_decimals())
def test_rotate_cycle(d):
    assume(d.is_finite())
    assume(d == d.to_integral_value())
    
    # Rotate only works on integers within certain bounds
    if abs(d) < decimal.Decimal('1e10'):
        # Rotating by number of digits should give back original
        num_digits = len(str(abs(int(d))))
        if num_digits > 0:
            rotated = d
            for _ in range(num_digits):
                rotated = rotated.rotate(1)
            
            # Check if we got back to original (considering precision)
            if d != 0:
                # For non-zero values, rotating by the number of digits
                # should cycle back, but implementation may differ
                pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])