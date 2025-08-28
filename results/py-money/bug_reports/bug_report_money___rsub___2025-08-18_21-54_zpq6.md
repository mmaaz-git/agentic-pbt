# Bug Report: money module - Incorrect __rsub__ Implementation

**Target**: `money.money.Money.__rsub__`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `__rsub__` method in the Money class incorrectly computes `self - other` instead of `other - self`, violating Python's reverse operator protocol.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from money.money import Money
from money.currency import Currency

@given(
    amount1=st.decimals(min_value=-1000, max_value=1000, places=2).map(str),
    amount2=st.decimals(min_value=-1000, max_value=1000, places=2).map(str)
)
def test_rsub_correctness(amount1, amount2):
    m1 = Money(amount1, Currency.USD)
    m2 = Money(amount2, Currency.USD)
    
    # m2.__rsub__(m1) should compute m1 - m2
    rsub_result = m2.__rsub__(m1)
    expected_result = m1 - m2
    
    assert rsub_result == expected_result
```

**Failing input**: Any two different amounts, e.g., `amount1="10.00", amount2="3.00"`

## Reproducing the Bug

```python
from money.money import Money
from money.currency import Currency

m1 = Money("10.00", Currency.USD)
m2 = Money("3.00", Currency.USD)

# Expected: m2.__rsub__(m1) should compute m1 - m2 = 7.00
# Actual: m2.__rsub__(m1) computes m2 - m1 = -7.00

rsub_result = m2.__rsub__(m1)
expected = Money("7.00", Currency.USD)
actual = Money("-7.00", Currency.USD)

print(f"m2.__rsub__(m1) = {rsub_result.amount}")  # -7.00
print(f"Expected: {expected.amount}")  # 7.00
print(f"Actual: {actual.amount}")  # -7.00

assert rsub_result == actual  # Bug: returns wrong value
```

## Why This Is A Bug

Python's data model specifies that `__rsub__` implements the reflected subtraction operation. When `a - b` is evaluated and `a` doesn't support subtraction with `b`, Python tries `b.__rsub__(a)`, which should still compute `a - b`. The current implementation returns `b - a` instead, producing the wrong result with the opposite sign.

## Fix

```diff
--- a/money/money.py
+++ b/money/money.py
@@ -106,7 +106,7 @@ class Money:
         return self.__class__(str(self.amount - other.amount), self.currency)
 
     def __rsub__(self, other: 'Money') -> 'Money':
-        return self.__sub__(other)
+        return other.__sub__(self)
```