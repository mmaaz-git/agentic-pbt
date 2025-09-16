# Bug Report: dateutil.tz.tzical Invalid Timezone Offset Validation

**Target**: `dateutil.tz.tzical._parse_offset`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_parse_offset` method in `dateutil.tz.tzical` accepts invalid time offset values without validation, allowing hours > 23 and minutes > 59, resulting in nonsensical timezone offsets that violate timezone standards.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import dateutil.tz
from io import StringIO
import pytest

def get_tzical():
    ical_content = """BEGIN:VTIMEZONE
TZID:Test/Zone
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE"""
    return dateutil.tz.tzical(StringIO(ical_content))

@given(st.text(alphabet='0123456789+-', min_size=1, max_size=8))
def test_parse_offset_validates_bounds(s):
    tzical = get_tzical()
    try:
        result = tzical._parse_offset(s)
        # Offset should be within ±24 hours
        assert -86400 <= result <= 86400
    except ValueError:
        pass  # Expected for invalid formats
```

**Failing input**: `'2401'` (and many others like `'9999'`, `'2500'`, `'0099'`)

## Reproducing the Bug

```python
import dateutil.tz
from io import StringIO
from datetime import datetime

ical_content = """BEGIN:VTIMEZONE
TZID:Invalid/Zone  
BEGIN:STANDARD
DTSTART:20200101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+2599
END:STANDARD
END:VTIMEZONE"""

tzical = dateutil.tz.tzical(StringIO(ical_content))
tz = tzical.get('Invalid/Zone')

dt = datetime(2020, 6, 15, 12, 0, 0)
offset = tz.utcoffset(dt)
print(f"UTC offset: {offset}")
print(f"Hours: {offset.total_seconds()/3600}")
```

## Why This Is A Bug

The IANA Time Zone Database and RFC 5545 (iCalendar specification) expect timezone offsets to represent valid time values. Accepting values like "+2599" (25 hours, 99 minutes) violates these standards and creates timezones with offsets exceeding 24 hours, which is physically impossible and breaks timezone arithmetic assumptions.

## Fix

```diff
--- a/dateutil/tz/tz.py
+++ b/dateutil/tz/tz.py
@@ -1321,10 +1321,20 @@ class tzical(object):
         else:
             signal = +1
         if len(s) == 4:
-            return (int(s[:2]) * 3600 + int(s[2:]) * 60) * signal
+            hours = int(s[:2])
+            minutes = int(s[2:])
+            if not (0 <= hours <= 23):
+                raise ValueError("invalid offset: " + s + " (hours must be 0-23)")
+            if not (0 <= minutes <= 59):
+                raise ValueError("invalid offset: " + s + " (minutes must be 0-59)")
+            return (hours * 3600 + minutes * 60) * signal
         elif len(s) == 6:
-            return (int(s[:2]) * 3600 + int(s[2:4]) * 60 + int(s[4:])) * signal
+            hours = int(s[:2])
+            minutes = int(s[2:4])
+            seconds = int(s[4:])
+            if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
+                raise ValueError("invalid offset: " + s)
+            return (hours * 3600 + minutes * 60 + seconds) * signal
         else:
             raise ValueError("invalid offset: " + s)
```