"""Property-based tests for money.money module using Hypothesis"""

import sys
import math
from decimal import Decimal
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from money.money import Money
from money.currency import Currency, CurrencyHelper
from money.exceptions import InvalidAmountError, CurrencyMismatchError, InvalidOperandError


# Strategy for generating valid currencies
currencies = st.sampled_from(list(Currency))

@composite
def valid_money_amounts(draw, currency=None):
    """Generate valid money amounts for a given currency"""
    if currency is None:
        currency = draw(currencies)
    
    # Get the decimal precision for this currency
    decimal_precision = CurrencyHelper.decimal_precision_for_currency(currency)
    
    # Generate amounts with appropriate precision
    if decimal_precision == 0:
        # No decimal places
        amount = draw(st.integers(min_value=-1000000, max_value=1000000))
        return str(amount)
    else:
        # Generate with correct decimal places
        multiplier = 10 ** decimal_precision
        int_val = draw(st.integers(min_value=-1000000 * multiplier, max_value=1000000 * multiplier))
        decimal_val = Decimal(int_val) / Decimal(multiplier)
        return str(decimal_val)

@composite
def money_objects(draw, currency=None):
    """Generate valid Money objects"""
    if currency is None:
        currency = draw(currencies)
    amount = draw(valid_money_amounts(currency=currency))
    return Money(amount, currency)


# Test 1: Sub-units round-trip property
@given(money_objects())
def test_sub_units_round_trip(m):
    """Test that converting to sub-units and back preserves the value"""
    sub_units = m.sub_units
    reconstructed = Money.from_sub_units(sub_units, m.currency)
    assert reconstructed == m, f"Round-trip failed: {m} != {reconstructed}"


# Test 2: Hash consistency with equality
@given(money_objects(), money_objects())
def test_hash_consistency(m1, m2):
    """Test that equal objects have equal hashes"""
    if m1 == m2:
        assert hash(m1) == hash(m2), f"Equal objects have different hashes: {m1}, {m2}"


# Test 3: Addition commutativity
@given(money_objects(), money_objects())
def test_addition_commutative(m1, m2):
    """Test that addition is commutative: a + b == b + a"""
    assume(m1.currency == m2.currency)  # Only test with same currency
    result1 = m1 + m2
    result2 = m2 + m1
    assert result1 == result2, f"{m1} + {m2} != {m2} + {m1}"


# Test 4: Multiplication commutativity with scalars
@given(money_objects(), st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
def test_multiplication_commutative(m, scalar):
    """Test that multiplication is commutative: m * x == x * m"""
    result1 = m * scalar
    result2 = scalar * m
    assert result1 == result2, f"{m} * {scalar} != {scalar} * {m}"


# Test 5: Division and multiplication inverse
@given(money_objects(), st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False))
def test_division_multiplication_inverse(m, scalar):
    """Test that division and multiplication are inverse operations"""
    multiplied = m * scalar
    divided_back = multiplied / scalar
    # Use approximate equality due to rounding
    assert abs(divided_back.amount - m.amount) < Decimal('0.01'), \
           f"({m} * {scalar}) / {scalar} != {m}, got {divided_back}"


# Test 6: Negation properties
@given(money_objects())
def test_double_negation(m):
    """Test that double negation returns the original: --m == m"""
    double_neg = -(-m)
    assert double_neg == m, f"--({m}) != {m}, got {double_neg}"


@given(money_objects())
def test_negation_addition_identity(m):
    """Test that m + (-m) == 0"""
    negated = -m
    result = m + negated
    zero = Money("0", m.currency)
    assert result == zero, f"{m} + (-{m}) != 0, got {result}"


# Test 7: Absolute value properties
@given(money_objects())
def test_abs_idempotence(m):
    """Test that abs(abs(m)) == abs(m)"""
    abs_once = abs(m)
    abs_twice = abs(abs_once)
    assert abs_once == abs_twice, f"abs(abs({m})) != abs({m})"


@given(money_objects())
def test_abs_negation_invariant(m):
    """Test that abs(-m) == abs(m)"""
    abs_positive = abs(m)
    abs_negative = abs(-m)
    assert abs_positive == abs_negative, f"abs({m}) != abs(-{m})"


# Test 8: Comparison transitivity
@given(money_objects(), money_objects(), money_objects())
def test_comparison_transitivity(a, b, c):
    """Test transitivity of less-than comparison"""
    assume(a.currency == b.currency == c.currency)
    if a < b and b < c:
        assert a < c, f"Transitivity violated: {a} < {b} and {b} < {c} but not {a} < {c}"


# Test 9: Total ordering
@given(money_objects(), money_objects())
def test_total_ordering(a, b):
    """Test that for any two Money objects with same currency, exactly one comparison is true"""
    assume(a.currency == b.currency)
    comparisons = [a < b, a == b, a > b]
    true_count = sum(comparisons)
    assert true_count == 1, f"Total ordering violated for {a} and {b}: {comparisons}"


# Test 10: Boolean conversion
@given(currencies)
def test_boolean_zero_is_false(currency):
    """Test that zero money is falsy"""
    zero = Money("0", currency)
    assert not bool(zero), f"Money('0', {currency}) should be falsy"


@given(money_objects())
def test_boolean_nonzero_is_true(m):
    """Test that non-zero money is truthy"""
    assume(m.amount != 0)
    assert bool(m), f"{m} should be truthy"


# Test 11: Constructor validation
@given(currencies, st.text(min_size=1, max_size=20))
def test_constructor_validation(currency, amount_str):
    """Test that constructor properly validates amounts"""
    try:
        m = Money(amount_str, currency)
        # If it succeeds, verify the amount is properly rounded
        decimal_precision = CurrencyHelper.decimal_precision_for_currency(currency)
        # The amount should have at most the allowed decimal places
        amount_decimal = Decimal(amount_str)
        if decimal_precision == 0:
            # Should be an integer
            assert amount_decimal == amount_decimal.to_integral_value(), \
                   f"Currency {currency} should not have decimal places"
    except (InvalidAmountError, ValueError, Exception):
        # Expected for invalid amounts
        pass


# Test 12: Same currency operations
@given(money_objects(), money_objects())
def test_different_currency_operations_fail(m1, m2):
    """Test that operations with different currencies raise CurrencyMismatchError"""
    assume(m1.currency != m2.currency)
    
    # All these should raise CurrencyMismatchError
    try:
        _ = m1 + m2
        assert False, f"Addition should fail for different currencies"
    except CurrencyMismatchError:
        pass
    
    try:
        _ = m1 - m2
        assert False, f"Subtraction should fail for different currencies"
    except CurrencyMismatchError:
        pass
    
    try:
        _ = m1 < m2
        assert False, f"Comparison should fail for different currencies"
    except CurrencyMismatchError:
        pass


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])