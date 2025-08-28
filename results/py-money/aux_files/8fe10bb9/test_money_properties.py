"""Property-based tests for the money module using Hypothesis"""

import math
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
from money import Money, Currency, InvalidAmountError, CurrencyMismatchError

# Strategy for valid currency amounts based on their precision
def valid_amount_for_currency(currency):
    """Generate valid amount strings for a given currency"""
    precision = {
        Currency.USD: 2,
        Currency.EUR: 2,
        Currency.GBP: 2,
        Currency.JPY: 0,  # No decimal places for JPY
        Currency.BHD: 3,  # 3 decimal places
        Currency.BYR: 0,  # No decimal places
        Currency.VUV: 0,  # No decimal places
    }.get(currency, 2)
    
    if precision == 0:
        # For currencies with no decimal places
        return st.integers(min_value=-1000000, max_value=1000000).map(str)
    else:
        # Generate amounts with proper decimal precision
        multiplier = 10 ** precision
        return st.integers(min_value=-100000000, max_value=100000000).map(
            lambda x: str(Decimal(x) / multiplier)
        )

# Test currencies - using a subset for efficiency
test_currencies = st.sampled_from([
    Currency.USD, Currency.EUR, Currency.GBP, 
    Currency.JPY, Currency.BHD, Currency.BYR
])

# Strategy for creating valid Money objects
@st.composite
def money_strategy(draw):
    currency = draw(test_currencies)
    amount = draw(valid_amount_for_currency(currency))
    try:
        return Money(amount, currency)
    except InvalidAmountError:
        # Skip invalid amounts
        assume(False)

# Test 1: Round-trip property for sub-units conversion
@given(money_strategy())
def test_sub_units_round_trip(money):
    """Test that converting to sub-units and back preserves the value"""
    sub_units = money.sub_units
    reconstructed = Money.from_sub_units(sub_units, money.currency)
    
    # The amounts should be equal
    assert reconstructed.amount == money.amount
    assert reconstructed.currency == money.currency
    assert reconstructed == money

# Test 2: Commutativity of addition
@given(money_strategy(), money_strategy())
def test_addition_commutative(m1, m2):
    """Test that m1 + m2 == m2 + m1"""
    assume(m1.currency == m2.currency)  # Only test with same currency
    
    result1 = m1 + m2
    result2 = m2 + m1
    
    assert result1 == result2
    assert result1.amount == result2.amount
    assert result1.currency == m1.currency

# Test 3: Identity property for addition
@given(money_strategy())
def test_addition_identity(money):
    """Test that m + 0 == m"""
    zero = Money("0", money.currency)
    result = money + zero
    
    assert result == money
    assert result.amount == money.amount

# Test 4: Inverse property for addition
@given(money_strategy())
def test_addition_inverse(money):
    """Test that m + (-m) == 0"""
    neg_money = -money
    result = money + neg_money
    zero = Money("0", money.currency)
    
    assert result == zero
    assert result.amount == Decimal("0")

# Test 5: Absolute value property
@given(money_strategy())
def test_absolute_value(money):
    """Test that abs(money) always has non-negative amount"""
    abs_money = abs(money)
    
    assert abs_money.amount >= 0
    assert abs_money.currency == money.currency
    
    # abs(abs(x)) == abs(x) (idempotence)
    assert abs(abs_money) == abs_money

# Test 6: Comparison transitivity
@given(money_strategy(), money_strategy(), money_strategy())
def test_comparison_transitivity(m1, m2, m3):
    """Test that if m1 < m2 and m2 < m3, then m1 < m3"""
    assume(m1.currency == m2.currency == m3.currency)
    
    if m1 < m2 and m2 < m3:
        assert m1 < m3
    
    if m1 <= m2 and m2 <= m3:
        assert m1 <= m3

# Test 7: Total ordering property
@given(money_strategy(), money_strategy())
def test_total_ordering(m1, m2):
    """Test that either m1 <= m2 or m2 <= m1 (or both)"""
    assume(m1.currency == m2.currency)
    
    # At least one of these must be true
    assert (m1 <= m2) or (m2 <= m1)
    
    # If both are true, they must be equal
    if (m1 <= m2) and (m2 <= m1):
        assert m1 == m2

# Test 8: Hash consistency with equality
@given(money_strategy(), money_strategy())
def test_hash_consistency(m1, m2):
    """Test that equal Money objects have equal hashes"""
    assume(m1.currency == m2.currency)
    
    if m1 == m2:
        assert hash(m1) == hash(m2)

# Test 9: Multiplication by scalar
@given(money_strategy(), st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
def test_multiplication_scalar(money, scalar):
    """Test multiplication by scalar preserves currency and scales amount correctly"""
    try:
        result = money * scalar
        assert result.currency == money.currency
        
        # Test commutativity with scalar
        result2 = scalar * money
        assert result == result2
        
        # Test identity
        identity_result = money * 1
        assert identity_result == money
        
    except (InvalidAmountError, ValueError, OverflowError):
        # Some multiplications might create invalid amounts
        pass

# Test 10: Division properties
@given(money_strategy(), st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False))
def test_division_scalar(money, divisor):
    """Test division by scalar preserves currency"""
    try:
        result = money / divisor
        assert result.currency == money.currency
        
        # m / 1 == m
        identity_result = money / 1
        assert identity_result == money
        
    except (InvalidAmountError, ValueError):
        # Some divisions might create invalid amounts
        pass

# Test 11: Division by Money returns float
@given(money_strategy(), money_strategy())
def test_division_by_money(m1, m2):
    """Test that dividing Money by Money returns a float ratio"""
    assume(m1.currency == m2.currency)
    assume(m2.amount != 0)  # Avoid division by zero
    
    result = m1 / m2
    assert isinstance(result, float)
    
    # The ratio should be correct
    expected_ratio = float(m1.amount / m2.amount)
    assert math.isclose(result, expected_ratio, rel_tol=1e-9)

# Test 12: Negation is self-inverse
@given(money_strategy())
def test_negation_self_inverse(money):
    """Test that -(-m) == m"""
    double_neg = -(-money)
    assert double_neg == money
    assert double_neg.amount == money.amount

# Test 13: Boolean conversion
@given(money_strategy())
def test_boolean_conversion(money):
    """Test that bool(money) is False only for zero amount"""
    if money.amount == 0:
        assert not bool(money)
    else:
        assert bool(money)

# Test 14: repr and hash relationship
@given(money_strategy())
def test_repr_format(money):
    """Test that repr follows expected format"""
    repr_str = repr(money)
    # Should be in format "CURRENCY_CODE amount"
    assert money.currency.name in repr_str
    assert str(money.amount) in repr_str

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])