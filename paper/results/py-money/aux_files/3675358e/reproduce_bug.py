#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.currency import Currency, CurrencyHelper
from money.money import Money
from decimal import Decimal

print("Demonstrating the bug with inconsistent sub_unit and decimal_precision")
print("=" * 80)

# Let's test with a few of the problematic currencies
test_currencies = [Currency.UGX, Currency.ISK, Currency.KRW]

for currency in test_currencies:
    print(f"\nTesting {currency.name} ({CurrencyHelper._CURRENCY_DATA[currency]['display_name']}):")
    print(f"  Decimal precision: {CurrencyHelper.decimal_precision_for_currency(currency)}")
    print(f"  Sub unit: {CurrencyHelper.sub_unit_for_currency(currency)}")
    
    # Test creating money from sub_units and converting back
    print("\n  Testing from_sub_units and sub_units property:")
    sub_units_input = 123
    money = Money.from_sub_units(sub_units_input, currency)
    print(f"    Input sub_units: {sub_units_input}")
    print(f"    Money amount: {money.amount}")
    print(f"    Back to sub_units: {money.sub_units}")
    
    # Check if round-trip works
    if sub_units_input != money.sub_units:
        print(f"    ❌ BUG: Round-trip failed! {sub_units_input} != {money.sub_units}")
    
    # Test the _round method's behavior
    print("\n  Testing rounding behavior:")
    test_amounts = ["1.23", "1.234", "1.235", "1.236"]
    for amount_str in test_amounts:
        try:
            money = Money(amount_str, currency)
            print(f"    Amount {amount_str} -> {money.amount}")
        except Exception as e:
            print(f"    Amount {amount_str} -> ERROR: {e}")

print("\n" + "=" * 80)
print("Analysis:")
print("-" * 80)
print("The bug causes issues because:")
print("1. Currencies with 0 decimal places (like UGX, ISK, KRW) have sub_unit=100")
print("2. This means they internally think 100 sub-units = 1 unit")
print("3. But with 0 decimal places, they shouldn't have sub-units at all (sub_unit should be 1)")
print("4. This creates confusion in the from_sub_units and sub_units methods")