#!/usr/bin/env python3
"""Direct execution of property tests"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from decimal import Decimal
from money.money import Money
from money.currency import Currency

print("Direct testing of money module properties...")
print("=" * 60)

# Test 1: Basic sub-units round trip
print("\nTest 1: Sub-units round trip")
try:
    # Test with USD (2 decimal places)
    m1 = Money("10.25", Currency.USD)
    sub_units = m1.sub_units  # Should be 1025 cents
    m2 = Money.from_sub_units(sub_units, Currency.USD)
    assert m1 == m2, f"USD round trip failed: {m1} != {m2}"
    print(f"  USD: 10.25 -> {sub_units} sub-units -> {m2.amount} ✓")
    
    # Test with JPY (0 decimal places)
    m3 = Money("1000", Currency.JPY)
    sub_units = m3.sub_units  # Should be 1000 (no sub-units for JPY)
    m4 = Money.from_sub_units(sub_units, Currency.JPY)
    assert m3 == m4, f"JPY round trip failed: {m3} != {m4}"
    print(f"  JPY: 1000 -> {sub_units} sub-units -> {m4.amount} ✓")
    
    # Test with BHD (3 decimal places)
    m5 = Money("10.123", Currency.BHD)
    sub_units = m5.sub_units  # Should be 10123 fils
    m6 = Money.from_sub_units(sub_units, Currency.BHD)
    assert m5 == m6, f"BHD round trip failed: {m5} != {m6}"
    print(f"  BHD: 10.123 -> {sub_units} sub-units -> {m6.amount} ✓")
    
    print("  ✓ Sub-units round trip works correctly")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Edge case - very small amounts
print("\nTest 2: Small amounts round trip")
try:
    # Test with 1 cent USD
    m1 = Money("0.01", Currency.USD)
    sub_units = m1.sub_units  # Should be 1
    m2 = Money.from_sub_units(sub_units, Currency.USD)
    assert m1 == m2, f"Small USD round trip failed: {m1} != {m2}"
    print(f"  USD: 0.01 -> {sub_units} sub-units -> {m2.amount} ✓")
    
    # Test with negative small amount
    m3 = Money("-0.01", Currency.USD)
    sub_units = m3.sub_units  # Should be -1
    m4 = Money.from_sub_units(sub_units, Currency.USD)
    assert m3 == m4, f"Negative small USD round trip failed: {m3} != {m4}"
    print(f"  USD: -0.01 -> {sub_units} sub-units -> {m4.amount} ✓")
    
    print("  ✓ Small amounts round trip works correctly")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Division by Money
print("\nTest 3: Division by Money returns float")
try:
    m1 = Money("10.00", Currency.USD)
    m2 = Money("2.50", Currency.USD)
    result = m1 / m2
    assert isinstance(result, float), f"Division didn't return float: {type(result)}"
    expected = 4.0
    assert result == expected, f"Division incorrect: {result} != {expected}"
    print(f"  10.00 USD / 2.50 USD = {result} (expected {expected}) ✓")
    
    print("  ✓ Division by Money works correctly")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 4: Hash consistency
print("\nTest 4: Hash consistency with equality")
try:
    m1 = Money("10.50", Currency.USD)
    m2 = Money("10.50", Currency.USD)
    assert m1 == m2, f"Equal money objects not equal: {m1} != {m2}"
    h1 = hash(m1)
    h2 = hash(m2)
    assert h1 == h2, f"Equal objects have different hashes: {h1} != {h2}"
    print(f"  Money(10.50, USD) hash consistency ✓")
    
    print("  ✓ Hash consistency works correctly")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 5: Addition inverse property
print("\nTest 5: Addition inverse (m + (-m) = 0)")
try:
    m1 = Money("10.50", Currency.USD)
    m2 = -m1
    result = m1 + m2
    zero = Money("0", Currency.USD)
    assert result == zero, f"m + (-m) != 0: {result} != {zero}"
    print(f"  10.50 USD + (-10.50 USD) = {result.amount} ✓")
    
    print("  ✓ Addition inverse works correctly")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 6: __rsub__ implementation
print("\nTest 6: Testing __rsub__ implementation")
try:
    m1 = Money("10.00", Currency.USD)
    m2 = Money("4.00", Currency.USD)
    
    # This should call __rsub__ on m2
    # But Python's data model doesn't call __rsub__ for same types
    # Let's test that __rsub__ exists and works
    result = m2.__rsub__(m1)  # Should be m1 - m2 according to the code
    expected = m1 - m2
    print(f"  m2.__rsub__(m1) = {result.amount}")
    print(f"  m1 - m2 = {expected.amount}")
    
    # But wait, the implementation is wrong!
    # __rsub__ should compute other - self, not self - other
    if result.amount != expected.amount:
        print(f"  ✗ BUG FOUND: __rsub__ implementation is incorrect!")
        print(f"    __rsub__ returns self - other instead of other - self")
    else:
        print("  ✓ __rsub__ works correctly")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing complete!")