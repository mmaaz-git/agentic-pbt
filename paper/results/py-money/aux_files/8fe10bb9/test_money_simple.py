#!/usr/bin/env python3
"""Simple property-based test runner for money module"""

import sys
import traceback
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
from hypothesis import Phase
from money.money import Money
from money.currency import Currency

# Use simpler settings for faster testing
settings.register_profile("fast", settings(max_examples=50, deadline=None, phases=[Phase.generate, Phase.target]))
settings.load_profile("fast")

# Focus on main currencies only
test_currencies = st.sampled_from([Currency.USD, Currency.EUR, Currency.JPY])

# Strategy for valid amounts
@st.composite
def money_strategy(draw):
    currency = draw(test_currencies)
    # Generate reasonable amounts
    if currency == Currency.JPY:
        # JPY has no decimal places
        amount = draw(st.integers(min_value=-10000, max_value=10000))
        amount_str = str(amount)
    else:
        # USD, EUR have 2 decimal places
        cents = draw(st.integers(min_value=-1000000, max_value=1000000))
        amount_str = str(Decimal(cents) / 100)
    
    return Money(amount_str, currency)

print("Running property-based tests for money module...")
print("=" * 60)

failures = []

# Test 1: Sub-units round trip
print("\n1. Testing sub-units round trip property...")
@given(money_strategy())
def test_sub_units_round_trip(money):
    sub_units = money.sub_units
    reconstructed = Money.from_sub_units(sub_units, money.currency)
    assert reconstructed == money, f"Round trip failed: {money} != {reconstructed}"

try:
    test_sub_units_round_trip()
    print("✓ Sub-units round trip test passed")
except Exception as e:
    print(f"✗ Sub-units round trip test FAILED: {e}")
    failures.append(("sub_units_round_trip", e))

# Test 2: Addition commutativity
print("\n2. Testing addition commutativity...")
@given(money_strategy(), money_strategy())
def test_addition_commutative(m1, m2):
    assume(m1.currency == m2.currency)
    result1 = m1 + m2
    result2 = m2 + m1
    assert result1 == result2, f"{m1} + {m2} != {m2} + {m1}"

try:
    test_addition_commutative()
    print("✓ Addition commutativity test passed")
except Exception as e:
    print(f"✗ Addition commutativity test FAILED: {e}")
    failures.append(("addition_commutative", e))

# Test 3: Negation is self-inverse
print("\n3. Testing negation self-inverse...")
@given(money_strategy())
def test_negation_inverse(money):
    double_neg = -(-money)
    assert double_neg == money, f"-(-{money}) != {money}"

try:
    test_negation_inverse()
    print("✓ Negation self-inverse test passed")
except Exception as e:
    print(f"✗ Negation self-inverse test FAILED: {e}")
    failures.append(("negation_inverse", e))

# Test 4: Division by money returns float
print("\n4. Testing division by money returns float...")
@given(money_strategy(), money_strategy())
def test_division_by_money(m1, m2):
    assume(m1.currency == m2.currency)
    assume(m2.amount != 0)
    result = m1 / m2
    assert isinstance(result, float), f"Division result not float: {type(result)}"
    expected = float(m1.amount / m2.amount)
    assert abs(result - expected) < 0.0001, f"Division incorrect: {result} != {expected}"

try:
    test_division_by_money()
    print("✓ Division by money test passed")
except Exception as e:
    print(f"✗ Division by money test FAILED: {e}")
    failures.append(("division_by_money", e))

# Test 5: Hash consistency
print("\n5. Testing hash consistency with equality...")
@given(money_strategy())
def test_hash_consistency(money):
    # Create identical money object
    same_money = Money(str(money.amount), money.currency)
    assert money == same_money, f"Equal money objects not equal: {money} != {same_money}"
    assert hash(money) == hash(same_money), f"Equal objects have different hashes"

try:
    test_hash_consistency()
    print("✓ Hash consistency test passed")
except Exception as e:
    print(f"✗ Hash consistency test FAILED: {e}")
    failures.append(("hash_consistency", e))

print("\n" + "=" * 60)
print(f"Results: {5 - len(failures)} passed, {len(failures)} failed")

if failures:
    print("\nFailed tests:")
    for name, error in failures:
        print(f"  - {name}: {error}")

sys.exit(len(failures))