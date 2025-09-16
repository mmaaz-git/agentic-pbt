# Bug Report: htmldate.extractors Invalid Date Handling

**Target**: `htmldate.extractors.custom_parse`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `custom_parse` function in htmldate.extractors silently converts invalid dates to the first day of the month instead of rejecting them, potentially leading to incorrect date extraction from web content.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from datetime import datetime
from htmldate.extractors import custom_parse

@given(
    st.integers(min_value=2020, max_value=2030),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=29, max_value=35)  # Days that may be invalid
)
def test_custom_parse_rejects_invalid_dates(year, month, day):
    """Test that custom_parse rejects invalid date strings"""
    date_string = f"{year:04d}-{month:02d}-{day:02d}"
    
    # Check if this is actually a valid date
    try:
        datetime(year, month, day)
        is_valid = True
    except ValueError:
        is_valid = False
    
    result = custom_parse(
        date_string,
        "%Y-%m-%d",
        datetime(2020, 1, 1),
        datetime(2030, 12, 31)
    )
    
    if not is_valid:
        # Invalid dates should return None, not be converted
        assert result is None, f"Invalid date {date_string} was converted to {result}"
```

**Failing input**: `custom_parse("2024-04-31", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2030, 12, 31))` returns `"2024-04-01"` instead of `None`

## Reproducing the Bug

```python
from datetime import datetime
from htmldate.extractors import custom_parse

invalid_dates = [
    "2024-02-30",  # February doesn't have 30 days
    "2024-04-31",  # April has only 30 days
    "2024-06-31",  # June has only 30 days
    "2024-12-00",  # Day cannot be 0
]

for date_string in invalid_dates:
    result = custom_parse(
        date_string,
        "%Y-%m-%d",
        datetime(2020, 1, 1),
        datetime(2030, 12, 31)
    )
    print(f"custom_parse('{date_string}') = {result}")
    # All return first of month instead of None
```

## Why This Is A Bug

The function should reject invalid dates like "2024-04-31" (April only has 30 days) by returning None. Instead, it silently converts them to valid dates (first of the month), which could lead to incorrect date extraction from web pages. This violates the principle of failing explicitly rather than silently accepting invalid input.

The bug occurs because after the YMD_PATTERN matches but datetime creation fails, the function continues to try YM_PATTERN which matches the year-month portion and creates a date with day=1, effectively discarding the invalid day component.

## Fix

```diff
--- a/htmldate/extractors.py
+++ b/htmldate/extractors.py
@@ -334,6 +334,7 @@ def custom_parse(
 
     # 3. Try the very common YMD, Y-M-D, and D-M-Y patterns
     match = YMD_PATTERN.search(string)
+    ymd_attempted = False
     if match:
+        ymd_attempted = True
         try:
             if match.lastgroup == "day":
                 year, month, day = (
@@ -359,7 +360,11 @@ def custom_parse(
                 LOGGER.debug("regex match: %s", candidate)
                 return candidate.strftime(outputformat)
 
     # 4. Try the Y-M and M-Y patterns
+    # Skip if we already tried YMD and it failed due to invalid date
+    if ymd_attempted:
+        return None
+        
     match = YM_PATTERN.search(string)
     if match:
         try:
```