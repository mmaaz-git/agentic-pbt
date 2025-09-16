# Bug Report: htmldate.validators AttributeError in validate_and_convert

**Target**: `htmldate.validators.validate_and_convert`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `validate_and_convert` function crashes with AttributeError when passed a valid date string, attempting to call `strftime()` on a string object instead of a datetime object.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from datetime import datetime
from htmldate.validators import validate_and_convert

@given(
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2099, 12, 31))
)
def test_validate_and_convert_round_trip(date_input):
    min_date = datetime(1900, 1, 1)
    max_date = datetime(2100, 1, 1)
    
    date_str = date_input.strftime("%Y-%m-%d")
    result = validate_and_convert(date_str, "%Y-%m-%d", min_date, max_date)
    
    if result is not None:
        parsed = datetime.strptime(result, "%Y-%m-%d")
        assert parsed.date() == date_input.date()
```

**Failing input**: Any valid date string, e.g., `"2000-01-01"`

## Reproducing the Bug

```python
from datetime import datetime
from htmldate.validators import validate_and_convert

min_date = datetime(1900, 1, 1)
max_date = datetime(2100, 1, 1)
date_str = "2000-01-01"

result = validate_and_convert(date_str, "%Y-%m-%d", min_date, max_date)
```

## Why This Is A Bug

The function signature indicates it accepts `Union[datetime, str]` for `date_input`, but the implementation always calls `date_input.strftime()` without checking the type. When a string is passed (which is valid per the type hint), it crashes with AttributeError since strings don't have a `strftime` method.

## Fix

```diff
--- a/htmldate/validators.py
+++ b/htmldate/validators.py
@@ -66,8 +66,14 @@ def validate_and_convert(
     "Robust validation and conversion for plausible dates."
     if is_valid_date(date_input, outputformat, earliest, latest):
         try:
             LOGGER.debug("custom parse result: %s", date_input)
-            return date_input.strftime(outputformat)  # type: ignore
+            # Convert string to datetime if needed
+            if isinstance(date_input, str):
+                # Parse the date string first
+                date_obj = datetime.strptime(date_input, outputformat)
+                return date_obj.strftime(outputformat)
+            else:
+                return date_input.strftime(outputformat)
         except ValueError as err:  # pragma: no cover
             LOGGER.error("value error during conversion: %s %s", date_input, err)
     return None
```