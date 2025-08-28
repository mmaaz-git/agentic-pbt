# Bug Report: quickbooks.helpers Year Padding Missing

**Target**: `quickbooks.helpers.qb_date_format`, `quickbooks.helpers.qb_datetime_format`, `quickbooks.helpers.qb_datetime_utc_offset_format`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Date formatting functions in quickbooks.helpers fail to zero-pad years with less than 4 digits, violating ISO 8601 standard and likely causing API compatibility issues.

## Property-Based Test

```python
import re
from datetime import datetime
from hypothesis import given, strategies as st
from quickbooks.helpers import qb_date_format

@given(st.datetimes(min_value=datetime(1, 1, 1), max_value=datetime(9999, 12, 31)))
def test_qb_date_format_pattern(dt):
    result = qb_date_format(dt)
    assert re.match(r'^\d{4}-\d{2}-\d{2}$', result), f"Format mismatch: {result}"
```

**Failing input**: `datetime(999, 1, 1, 0, 0)`

## Reproducing the Bug

```python
from datetime import datetime
from quickbooks.helpers import qb_date_format, qb_datetime_format, qb_datetime_utc_offset_format

dt_999 = datetime(999, 1, 1)
print(qb_date_format(dt_999))
print(qb_datetime_format(dt_999))
print(qb_datetime_utc_offset_format(dt_999, "+00:00"))

dt_9 = datetime(9, 12, 31)
print(qb_date_format(dt_9))
```

## Why This Is A Bug

The QuickBooks API and ISO 8601 standard expect dates in YYYY-MM-DD format with exactly 4-digit years. The current implementation returns "999-01-01" instead of "0999-01-01" for years with fewer than 4 digits. This violates the expected contract and will likely cause API errors or data parsing issues when these formatted dates are sent to QuickBooks or parsed by other systems expecting ISO 8601 compliance.

## Fix

```diff
def qb_date_format(input_date):
    """
    Converts date to quickbooks date format
    :param input_date:
    :return:
    """
-   return input_date.strftime("%Y-%m-%d")
+   # Ensure year is always 4 digits with zero padding
+   year = input_date.year
+   month = input_date.month
+   day = input_date.day
+   return f"{year:04d}-{month:02d}-{day:02d}"

def qb_datetime_format(input_date):
    """
    Converts datetime to quickbooks datetime format
    :param input_date:
    :return:
    """
-   return input_date.strftime("%Y-%m-%dT%H:%M:%S")
+   # Ensure year is always 4 digits with zero padding
+   year = input_date.year
+   month = input_date.month
+   day = input_date.day
+   hour = input_date.hour
+   minute = input_date.minute
+   second = input_date.second
+   return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
```