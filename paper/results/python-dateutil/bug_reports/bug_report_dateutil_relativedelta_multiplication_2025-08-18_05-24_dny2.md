# Bug Report: dateutil.relativedelta Multiplication Unexpectedly Normalizes Units

**Target**: `dateutil.relativedelta.__mul__`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Multiplying a relativedelta by a scalar unexpectedly normalizes time units (e.g., 12 months becomes 1 year), changing the semantic meaning of the delta.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from dateutil.relativedelta import relativedelta

@given(
    st.integers(min_value=-100, max_value=100),
    st.floats(min_value=-10, max_value=10, allow_nan=False)
)
@settings(max_examples=500)
def test_multiplication_preserves_units(months, scalar):
    rd = relativedelta(months=months)
    result = rd * scalar
    
    expected_months = int(months * scalar)
    expected_years, expected_months_remainder = divmod(expected_months, 12)
    
    # Should preserve the exact units without normalization
    assert result.months == expected_months
    assert result.years == 0
```

**Failing input**: `relativedelta(months=4) * 3.0`

## Reproducing the Bug

```python
from dateutil.relativedelta import relativedelta

rd = relativedelta(months=4)
result = rd * 3.0

print(f"relativedelta(months=4) * 3.0 = {result}")
print(f"Expected: relativedelta(months=+12)")
print(f"But got:  relativedelta(years=+1)")
```

## Why This Is A Bug

When multiplying `relativedelta(months=4)` by 3, users expect `relativedelta(months=12)`, not `relativedelta(years=1)`. The normalization changes the semantic meaning:
- `months=12` means "exactly 12 months from now"
- `years=1` means "same date next year" 

These have different behaviors around leap years and month boundaries. For example:
- 2024-02-29 + relativedelta(months=12) = 2025-02-28 (clamped to valid date)
- 2024-02-29 + relativedelta(years=1) = 2025-02-28 (same result, but conceptually different)

The issue is that users may rely on the specific unit representation for business logic.

## Fix

The `__mul__` method should preserve the original unit representation without calling `_fix()`:

```diff
--- a/dateutil/relativedelta.py
+++ b/dateutil/relativedelta.py
@@ -500,8 +500,10 @@ class relativedelta(object):
 
         return self.__class__(years=int(self.years * f),
                              months=int(self.months * f),
                              days=int(self.days * f),
                              hours=int(self.hours * f),
                              minutes=int(self.minutes * f),
                              seconds=int(self.seconds * f),
                              microseconds=int(self.microseconds * f),
                              leapdays=self.leapdays,
                              year=self.year,
                              month=self.month,
                              day=self.day,
                              weekday=self.weekday,
                              hour=self.hour,
                              minute=self.minute,
                              second=self.second,
-                             microsecond=self.microsecond)
+                             microsecond=self.microsecond,
+                             _skip_fix=True)  # Don't normalize after multiplication
```