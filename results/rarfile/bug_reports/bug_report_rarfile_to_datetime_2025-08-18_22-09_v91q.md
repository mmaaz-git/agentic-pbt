# Bug Report: rarfile to_datetime Incomplete Sanitization

**Target**: `rarfile.to_datetime`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_datetime` function fails to properly sanitize negative time values, raising ValueError instead of clamping them as documented.

## Property-Based Test

```python
@given(
    st.tuples(
        st.integers(min_value=1, max_value=9999),
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=-100, max_value=100),
    )
)
def test_to_datetime_sanitization(time_tuple):
    """to_datetime claims to sanitize invalid values - should never raise exception."""
    result = rarfile.to_datetime(time_tuple)
    assert isinstance(result, datetime)
```

**Failing input**: `time_tuple=(1, 0, 0, 0, 0, -1)`

## Reproducing the Bug

```python
import rarfile

time_tuple = (2020, 1, 1, 0, 0, -1)
result = rarfile.to_datetime(time_tuple)
```

## Why This Is A Bug

The function documentation and implementation attempt to "sanitize invalid values" in the except block (lines 3180-3187), but the sanitization logic uses `min()` without `max()` for hours, minutes, and seconds. This fails to handle negative values: `min(-1, 59)` returns `-1`, which is still invalid for datetime construction.

## Fix

```diff
def to_datetime(t):
    """Convert 6-part time tuple into datetime object.
    """
    # extract values
    year, mon, day, h, m, s = t

    # assume the values are valid
    try:
        return datetime(year, mon, day, h, m, s)
    except ValueError:
        pass

    # sanitize invalid values
    mday = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    mon = max(1, min(mon, 12))
    day = max(1, min(day, mday[mon]))
-    h = min(h, 23)
-    m = min(m, 59)
-    s = min(s, 59)
+    h = max(0, min(h, 23))
+    m = max(0, min(m, 59))
+    s = max(0, min(s, 59))
    return datetime(year, mon, day, h, m, s)
```