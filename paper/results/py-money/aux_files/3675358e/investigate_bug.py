#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.currency import Currency, CurrencyHelper

print("Investigating currencies with inconsistent decimal_precision and sub_unit:")
print("-" * 80)

inconsistent_currencies = []

for currency in Currency:
    data = CurrencyHelper._CURRENCY_DATA[currency]
    decimal_precision = data['default_fraction_digits']
    sub_unit = data['sub_unit']
    
    # Check if sub_unit matches expected value based on decimal_precision
    if sub_unit not in [1, 5]:  # Exclude special cases
        expected_sub_unit = 10 ** decimal_precision
        if sub_unit != expected_sub_unit:
            inconsistent_currencies.append({
                'currency': currency.name,
                'decimal_precision': decimal_precision,
                'sub_unit': sub_unit,
                'expected_sub_unit': expected_sub_unit
            })
            print(f"Currency: {currency.name}")
            print(f"  Decimal precision: {decimal_precision}")
            print(f"  Sub unit: {sub_unit}")
            print(f"  Expected sub unit: {expected_sub_unit}")
            print()

print(f"\nTotal inconsistent currencies found: {len(inconsistent_currencies)}")

# Let's also check what the standard says about these currencies
print("\n" + "=" * 80)
print("Detailed analysis of inconsistent currencies:")
print("=" * 80)

for item in inconsistent_currencies:
    currency = Currency[item['currency']]
    data = CurrencyHelper._CURRENCY_DATA[currency]
    print(f"\n{currency.name} - {data['display_name']}:")
    print(f"  Numeric code: {data['numeric_code']}")
    print(f"  Decimal precision: {data['default_fraction_digits']}")
    print(f"  Sub unit: {data['sub_unit']}")
    print(f"  Issue: Sub unit is {data['sub_unit']} but should be {item['expected_sub_unit']} based on decimal precision of {data['default_fraction_digits']}")