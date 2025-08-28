# Bug Report: money.currency Inconsistent Sub-Unit Configuration

**Target**: `money.currency`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

29 currencies have incorrectly configured sub_unit values that don't match their decimal precision, causing Money.from_sub_units() to fail for most input values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from money.currency import Currency, CurrencyHelper

@given(st.sampled_from(Currency))
def test_decimal_precision_sub_unit_consistency(currency):
    """Decimal precision and sub_unit should be consistent"""
    data = CurrencyHelper._CURRENCY_DATA[currency]
    decimal_precision = data['default_fraction_digits']
    sub_unit = data['sub_unit']
    
    if sub_unit not in [1, 5]:
        expected_sub_unit = 10 ** decimal_precision
        assert sub_unit == expected_sub_unit
```

**Failing input**: `Currency.UGX` (and 28 other currencies)

## Reproducing the Bug

```python
from money.currency import Currency
from money.money import Money

# UGX has 0 decimal places but sub_unit=100 (should be 1)
currency = Currency.UGX

# This fails with InvalidAmountError
money = Money.from_sub_units(50, currency)
```

## Why This Is A Bug

Currencies with 0 decimal places (like UGX, ISK, KRW) have their sub_unit incorrectly set to 100 instead of 1. This means Money.from_sub_units() divides by 100, creating fractional amounts that are invalid for zero-decimal currencies. The method fails for any input that isn't a multiple of 100.

## Fix

```diff
--- a/money/currency.py
+++ b/money/currency.py
@@ -286,7 +286,7 @@ class CurrencyHelper:
         Currency.BIF: {
             'display_name': 'Burundi Franc',
             'numeric_code': 108,
             'default_fraction_digits': 0,
-            'sub_unit': 100,
+            'sub_unit': 1,
         },
```

The same fix needs to be applied to all 29 affected currencies: BIF, CLF, CLP, DJF, GNF, ISK, KMF, KRW, PYG, RWF, UGX, UYI, VND (10), XAF, XAG, XAU, XBA, XBB, XBC, XBD, XDR, XFU, XOF, XPD, XPF, XPT, XSU, XTS, XUA.