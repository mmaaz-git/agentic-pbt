# Bug Report: htmldate.validators get_min_date doesn't enforce MIN_DATE boundary

**Target**: `htmldate.validators.get_min_date`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `get_min_date` function fails to enforce the MIN_DATE boundary when given a datetime before MIN_DATE, returning the input date instead of MIN_DATE.

## Property-Based Test

```python
@given(st.one_of(st.none(), 
                  st.datetimes(min_value=datetime(1900, 1, 1), 
                               max_value=datetime(2100, 1, 1))))
def test_get_min_date_respects_minimum(date_input):
    result = get_min_date(date_input)
    assert isinstance(result, datetime)
    if date_input is None:
        assert result == settings.MIN_DATE
    elif date_input < settings.MIN_DATE:
        assert result >= settings.MIN_DATE
```

**Failing input**: `datetime.datetime(1994, 1, 1, 0, 0)`

## Reproducing the Bug

```python
from datetime import datetime
from htmldate.settings import MIN_DATE
from htmldate.validators import get_min_date

test_date = datetime(1994, 1, 1, 0, 0)
result = get_min_date(test_date)

print(f"MIN_DATE: {MIN_DATE}")  # 1995-01-01 00:00:00
print(f"Input: {test_date}")     # 1994-01-01 00:00:00
print(f"Result: {result}")       # 1994-01-01 00:00:00 (BUG!)

assert result >= MIN_DATE  # AssertionError
```

## Why This Is A Bug

The `get_min_date` function's docstring states "Validates the minimum date and/or defaults to earliest plausible date". When given a date before MIN_DATE, it should enforce the minimum boundary and return MIN_DATE instead of the input date. This violates the expected contract of the function.

## Fix

```diff
--- a/htmldate/validators.py
+++ b/htmldate/validators.py
@@ -208,7 +208,10 @@ def check_date_input(
 
 def get_min_date(min_date: Optional[Union[datetime, str]]) -> datetime:
     """Validates the minimum date and/or defaults to earliest plausible date"""
-    return check_date_input(min_date, MIN_DATE)
+    result = check_date_input(min_date, MIN_DATE)
+    if result < MIN_DATE:
+        return MIN_DATE
+    return result
 
 
 def get_max_date(max_date: Optional[Union[datetime, str]]) -> datetime:
```