#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.currency import Currency, CurrencyHelper
from money.money import Money
from decimal import Decimal

print("Minimal bug reproduction:")
print("=" * 80)

# Test with UGX (Uganda Shilling)
currency = Currency.UGX
print(f"Currency: {currency.name}")
print(f"Decimal precision: {CurrencyHelper.decimal_precision_for_currency(currency)}")
print(f"Sub unit: {CurrencyHelper.sub_unit_for_currency(currency)}")

print("\nThe problem:")
print("- UGX has 0 decimal places (no fractional units)")
print("- But sub_unit is set to 100 (implies 2 decimal places)")
print("- This causes from_sub_units to fail")

print("\nAttempting Money.from_sub_units(100, Currency.UGX):")
try:
    money = Money.from_sub_units(100, Currency.UGX)
    print(f"Success: {money}")
except Exception as e:
    print(f"Failed with: {type(e).__name__}: {e}")

print("\nWhat happens internally:")
sub_units = 100
sub_units_per_unit = CurrencyHelper.sub_unit_for_currency(currency)
amount = Decimal(sub_units) / Decimal(sub_units_per_unit)
print(f"- sub_units = {sub_units}")
print(f"- sub_units_per_unit = {sub_units_per_unit}")
print(f"- calculated amount = {sub_units} / {sub_units_per_unit} = {amount}")

print("\nTrying to create Money with this amount:")
try:
    money = Money(str(amount), currency)
    print(f"Success: {money}")
except Exception as e:
    print(f"Failed with: {type(e).__name__}: {e}")

print("\nThe issue: Money(\"1.0\", Currency.UGX) fails because:")
print("- UGX has 0 decimal places")
print("- The _round method enforces this")
print("- So any non-integer amount is rejected")
print("- But from_sub_units creates fractional amounts due to incorrect sub_unit value")