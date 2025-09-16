# Bug Report: htmldate.validators validate_and_convert AttributeError

**Target**: `htmldate.validators.validate_and_convert`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `validate_and_convert` function crashes with AttributeError when given valid date strings, attempting to call `strftime()` on string inputs instead of datetime objects.

## Property-Based Test

```python
from datetime import datetime
from hypothesis import given, strategies as st, settings
from htmldate import validators

valid_date_strings = st.builds(
    lambda y, m, d: f"{y:04d}-{m:02d}-{d:02d}",
    st.integers(min_value=2000, max_value=2024),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)
)

@given(date_string=valid_date_strings)
@settings(max_examples=100)
def test_validate_and_convert_with_strings(date_string):
    outputformat = "%Y-%m-%d"
    earliest = datetime(1995, 1, 1)
    latest = datetime(2030, 12, 31)
    
    if validators.is_valid_date(date_string, outputformat, earliest, latest):
        result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
        assert result is not None
```

**Failing input**: `"2024-01-15"`

## Reproducing the Bug

```python
from datetime import datetime
from htmldate import validators

date_string = "2024-01-15"
outputformat = "%Y-%m-%d"
earliest = datetime(2020, 1, 1)
latest = datetime(2025, 12, 31)

is_valid = validators.is_valid_date(date_string, outputformat, earliest, latest)
print(f"Date is valid: {is_valid}")

result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
```

## Why This Is A Bug

The function's type signature accepts `Union[datetime, str]` for the `date_input` parameter, and `is_valid_date` correctly handles both types. However, `validate_and_convert` unconditionally calls `date_input.strftime(outputformat)` on line 70, which fails for string inputs since strings don't have a `strftime` method. This causes the function to crash with valid date strings that pass the `is_valid_date` check.

## Fix

```diff
--- a/htmldate/validators.py
+++ b/htmldate/validators.py
@@ -67,7 +67,10 @@ def validate_and_convert(
     if is_valid_date(date_input, outputformat, earliest, latest):
         try:
             LOGGER.debug("custom parse result: %s", date_input)
-            return date_input.strftime(outputformat)  # type: ignore
+            if isinstance(date_input, datetime):
+                return date_input.strftime(outputformat)
+            else:
+                return date_input  # Already validated as correct format string
         except ValueError as err:  # pragma: no cover
             LOGGER.error("value error during conversion: %s %s", date_input, err)
     return None
```