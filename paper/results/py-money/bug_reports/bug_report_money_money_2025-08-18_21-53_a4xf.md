# Bug Report: money.money Multiplication/Division Inverse Violation

**Target**: `money.money.Money`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Money class violates the mathematical property that multiplication and division should be inverse operations due to intermediate rounding, causing `(m * x) / x != m` for certain values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from money.money import Money
from money.currency import Currency
from decimal import Decimal

@given(st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False))
def test_division_multiplication_inverse():
    m = Money("0.01", Currency.AED)
    scalar = 0.5
    multiplied = m * scalar
    divided_back = multiplied / scalar
    assert divided_back == m
```

**Failing input**: `Money("0.01", Currency.AED)` with scalar `0.5`

## Reproducing the Bug

```python
from money.money import Money
from money.currency import Currency

m = Money("0.01", Currency.AED)
scalar = 0.5

result = (m * scalar) / scalar
print(f"Original: {m}")
print(f"Result:   {result}")
print(f"Equal? {result == m}")
```

## Why This Is A Bug

When multiplying 0.01 by 0.5, the result (0.005) is rounded to 0.01. Dividing 0.01 by 0.5 then yields 0.02, not the original 0.01. This breaks the fundamental mathematical expectation that multiplication and division are inverse operations, which could lead to incorrect financial calculations in applications that rely on this property.

## Fix

The issue stems from aggressive rounding at each operation. A potential fix would be to maintain higher internal precision during chained operations or to provide methods that delay rounding until the final result. However, this would require significant architectural changes to track operation chains.

```diff
# Potential approach: Add a raw calculation mode that delays rounding
class Money:
+   def __init__(self, amount: str, currency: Currency=Currency.USD, _raw_amount: Decimal=None):
+       if _raw_amount is not None:
+           # Internal use: preserve full precision
+           self._raw_amount = _raw_amount
+           self._amount = self._round(_raw_amount, currency)
+       else:
+           self._amount = Decimal(amount)
+           self._raw_amount = self._amount
        
    def __mul__(self, other: float) -> 'Money':
        if isinstance(other, Money):
            raise InvalidOperandError
-       amount = self._round(self._amount * Decimal(other), self._currency)
-       return self.__class__(str(amount), self._currency)
+       raw = self._raw_amount * Decimal(other)
+       return self.__class__(str(self._round(raw, self._currency)), 
+                            self._currency, _raw_amount=raw)
```