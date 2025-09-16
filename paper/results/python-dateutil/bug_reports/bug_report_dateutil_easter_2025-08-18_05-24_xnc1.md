# Bug Report: dateutil.easter Invalid Date Generation Crash

**Target**: `dateutil.easter.easter`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `easter()` function crashes with `ValueError: day is out of range for month` when calculating Orthodox Easter (method=2) for certain years, attempting to create invalid dates like June 31st.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import dateutil.easter as easter
import datetime

@given(st.integers(min_value=1, max_value=9999), st.integers(min_value=1, max_value=3))
def test_valid_date_generation(year, method):
    """Easter calculation should always produce valid dates."""
    date = easter.easter(year, method)
    assert isinstance(date, datetime.date)
```

**Failing input**: `year=5243, method=2`

## Reproducing the Bug

```python
import dateutil.easter as easter

date = easter.easter(5243, 2)
```

## Why This Is A Bug

The algorithm calculates `d = 31` and `m = 6` for year 5243 with Orthodox method, attempting to create June 31st which doesn't exist. This causes an unhandled `ValueError` crash. The bug affects 137 years between 1 and 9999, including: 5243, 5395, 5463, 5536, 5615, 5699, 5767, 5778, 5835, 5840, and others.

## Fix

The issue occurs in the date calculation logic where the algorithm doesn't properly handle the case when `p` (days from March 21 to Easter) exceeds certain bounds. The calculation `d = 1 + (p + 27 + (p + 6)//40) % 31` can produce day 31 for June.

```diff
--- a/dateutil/easter.py
+++ b/dateutil/easter.py
@@ -86,5 +86,11 @@ def easter(year, method=EASTER_WESTERN):
     p = i - j + e
     d = 1 + (p + 27 + (p + 6)//40) % 31
     m = 3 + (p + 26)//30
+    
+    # Handle June 31st edge case
+    if m == 6 and d == 31:
+        m = 7
+        d = 1
+    
     return datetime.date(int(y), int(m), int(d))
```