# Bug Report: dateutil.relativedelta Inverse Property Violation

**Target**: `dateutil.relativedelta`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The relativedelta class violates the mathematical inverse property: adding a relativedelta and then subtracting the same relativedelta does not always return the original date.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dateutil import relativedelta
import datetime

@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-12, max_value=12),
    st.integers(min_value=-100, max_value=100)
)
def test_relativedelta_inverse(years, months, days):
    """Test that adding and subtracting same relativedelta is identity"""
    rd = relativedelta.relativedelta(years=years, months=months, days=days)
    base = datetime.datetime(2020, 6, 15)
    
    result = base + rd - rd
    assert result == base
```

**Failing input**: `years=0, months=1, days=-15`

## Reproducing the Bug

```python
from dateutil import relativedelta
import datetime

base = datetime.datetime(2020, 6, 15)
rd = relativedelta.relativedelta(months=1, days=-15)

print(f"Base date: {base}")
print(f"Relativedelta: {rd}")

intermediate = base + rd
print(f"Base + rd: {intermediate}")

final = intermediate - rd  
print(f"(Base + rd) - rd: {final}")

print(f"Should equal base? {final == base}")
print(f"Actual difference: {(final - base).days} days")
```

Output:
```
Base date: 2020-06-15 00:00:00
Relativedelta: relativedelta(months=+1, days=-15)
Base + rd: 2020-06-30 00:00:00
(Base + rd) - rd: 2020-06-14 00:00:00
Should equal base? False
Actual difference: -1 days
```

## Why This Is A Bug

The issue occurs because relativedelta applies operations in a specific order:
1. Month/year arithmetic is applied first
2. Day/time arithmetic is applied second

When adding `relativedelta(months=1, days=-15)` to 2020-06-15:
- First: Add 1 month → 2020-07-15
- Then: Subtract 15 days → 2020-06-30

When subtracting the same relativedelta from 2020-06-30:
- First: Subtract 1 month → 2020-05-30  
- Then: Add 15 days → 2020-06-14

This violates the expected mathematical property that `(x + y) - y = x`. Users would reasonably expect that adding and subtracting the same time delta would be inverse operations, especially since this property holds for standard `datetime.timedelta` objects.

## Fix

The fix would require either:
1. Documenting this non-intuitive behavior clearly in the relativedelta documentation
2. Implementing a true inverse operation for subtraction that reverses the order of operations
3. Tracking the order of operations internally to properly reverse them

A documentation fix would be simplest:

```diff
--- a/dateutil/relativedelta.py
+++ b/dateutil/relativedelta.py
@@ -10,6 +10,11 @@ class relativedelta:
     in his
     `mx.DateTime <https://www.egenix.com/products/python/mxBase/mxDateTime/>`_ extension.
     However, notice that this type does *NOT* implement the same algorithm as
     his work. Do *NOT* expect it to behave like mx.DateTime's counterpart.
+    
+    .. warning::
+        Adding and subtracting the same relativedelta is not always an identity operation
+        when mixing month and day arithmetic, as months are applied before days in both
+        addition and subtraction. For example: (date + relativedelta(months=1, days=-15)) - 
+        relativedelta(months=1, days=-15) may not equal the original date.
```