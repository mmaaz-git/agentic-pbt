# Bug Report: dateutil.utils.within_delta TypeError with Mixed Timezone Awareness

**Target**: `dateutil.utils.within_delta`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `within_delta` function crashes with a `TypeError` when comparing datetimes with different timezone awareness (one naive, one aware).

## Property-Based Test

```python
from datetime import datetime, timedelta
from hypothesis import given, strategies as st
import dateutil.utils

datetime_strategy = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2200, 12, 31),
    timezones=st.none() | st.timezones()
)

timedelta_strategy = st.timedeltas(
    min_value=timedelta(microseconds=-10**15),
    max_value=timedelta(microseconds=10**15)
)

@given(datetime_strategy, datetime_strategy, timedelta_strategy)
def test_within_delta_symmetry(dt1, dt2, delta):
    """within_delta(a, b, d) should equal within_delta(b, a, d)"""
    result1 = dateutil.utils.within_delta(dt1, dt2, delta)
    result2 = dateutil.utils.within_delta(dt2, dt1, delta)
    assert result1 == result2
```

**Failing input**: `dt1=datetime(2000, 1, 1, 0, 0), dt2=datetime(2000, 1, 1, 0, 0, tzinfo=UTC), delta=timedelta(0)`

## Reproducing the Bug

```python
from datetime import datetime, timedelta, timezone
from dateutil.utils import within_delta

naive_dt = datetime(2000, 1, 1, 0, 0)
aware_dt = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)
delta = timedelta(0)

result = within_delta(naive_dt, aware_dt, delta)
```

## Why This Is A Bug

The `within_delta` function should handle comparisons between naive and aware datetimes gracefully. While Python's datetime subtraction raises a TypeError for mixed timezone awareness, a utility function for checking if datetimes are "close enough" should either:
1. Return False when comparing incompatible datetimes
2. Raise a more informative error message
3. Document this limitation clearly

Currently, the function crashes with an unhelpful error that exposes implementation details.

## Fix

```diff
def within_delta(dt1, dt2, delta):
    """
    Useful for comparing two datetimes that may have a negligible difference
    to be considered equal.
    """
    delta = abs(delta)
-   difference = dt1 - dt2
+   try:
+       difference = dt1 - dt2
+   except TypeError:
+       # Cannot compare naive and aware datetimes
+       return False
    return -delta <= difference <= delta
```