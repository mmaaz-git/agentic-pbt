# Bug Report: datetime.date Silently Discards Time Components from Timedelta

**Target**: `datetime.date.__add__`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When adding a timedelta with time components (hours, minutes, seconds) to a date object, the time components are silently discarded, violating associativity and the principle of least surprise.

## Property-Based Test

```python
import datetime
from hypothesis import given, strategies as st, settings

@given(
    st.dates(),
    st.timedeltas(),
    st.timedeltas()
)
@settings(max_examples=500)
def test_timedelta_associativity(d, td1, td2):
    try:
        result1 = (d + td1) + td2
        result2 = d + (td1 + td2)
        assert result1 == result2  # Fails!
    except OverflowError:
        pass
```

**Failing input**: `date(1, 1, 1), timedelta(seconds=1), timedelta(seconds=86399)`

## Reproducing the Bug

```python
import datetime

d = datetime.date(2024, 1, 1)
td1 = datetime.timedelta(hours=13)
td2 = datetime.timedelta(hours=12)

result1 = (d + td1) + td2
result2 = d + (td1 + td2)

print(f"(date + 13h) + 12h = {result1}")
print(f"date + (13h + 12h) = {result2}")
assert result1 != result2
```

## Why This Is A Bug

This violates the mathematical property of associativity: (a + b) + c should equal a + (b + c). When adding timedeltas to dates, the time components are silently truncated, causing:
- `(date + timedelta(hours=13)) + timedelta(hours=12)` → date (both additions lose time)
- `date + (timedelta(hours=13) + timedelta(hours=12))` → date + 1 day (25 hours = 1 day + 1 hour)

The silent loss of time data is unexpected and can lead to subtle bugs in date arithmetic.

## Fix

The issue is that `date.__add__` only uses the `days` component of the timedelta. Options to fix:

1. **Raise an error** when timedelta has non-zero time components:
```diff
def __add__(self, other):
    if isinstance(other, timedelta):
+       if other.seconds != 0 or other.microseconds != 0:
+           raise ValueError("Cannot add timedelta with time components to date")
        return date(self.year, self.month, self.day + other.days)
```

2. **Return a datetime** when time components are present:
```diff
def __add__(self, other):
    if isinstance(other, timedelta):
+       if other.seconds != 0 or other.microseconds != 0:
+           return datetime(self.year, self.month, self.day) + other
        return date(self.year, self.month, self.day + other.days)
```

3. **Document** this behavior clearly in the docstring (least preferred, as it maintains the surprising behavior)