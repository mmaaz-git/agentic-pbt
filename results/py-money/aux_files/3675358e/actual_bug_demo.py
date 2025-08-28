#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.currency import Currency, CurrencyHelper
from money.money import Money
from decimal import Decimal

print("Demonstrating the actual bug:")
print("=" * 80)

currency = Currency.UGX
print(f"Currency: {currency.name} (Uganda Shilling)")
print(f"Decimal precision: {CurrencyHelper.decimal_precision_for_currency(currency)}")
print(f"Sub unit: {CurrencyHelper.sub_unit_for_currency(currency)}")

print("\nThe bug manifests when using non-multiples of 100:")
print("-" * 40)

# Test various sub_unit values
test_values = [1, 50, 99, 100, 150, 199, 200]

for sub_units in test_values:
    print(f"\nTrying Money.from_sub_units({sub_units}, Currency.UGX):")
    try:
        money = Money.from_sub_units(sub_units, Currency.UGX)
        print(f"  Created: {money}")
        print(f"  Amount: {money.amount}")
        print(f"  Back to sub_units: {money.sub_units}")
        if sub_units != money.sub_units:
            print(f"  ⚠️  ISSUE: Input {sub_units} != Output {money.sub_units}")
    except Exception as e:
        print(f"  ❌ FAILED: {type(e).__name__}: {e}")
        # Show what amount was calculated
        sub_units_per_unit = CurrencyHelper.sub_unit_for_currency(currency)
        amount = Decimal(sub_units) / Decimal(sub_units_per_unit)
        print(f"  (Tried to create Money with amount={amount})")

print("\n" + "=" * 80)
print("Summary of the bug:")
print("-" * 80)
print("For currencies with 0 decimal places (like UGX, ISK, KRW):")
print("1. The sub_unit is incorrectly set to 100 instead of 1")
print("2. This causes from_sub_units to divide by 100")
print("3. Non-multiples of 100 produce fractional amounts")
print("4. These fractional amounts are invalid for 0-decimal currencies")
print("5. Result: from_sub_units fails for most inputs")