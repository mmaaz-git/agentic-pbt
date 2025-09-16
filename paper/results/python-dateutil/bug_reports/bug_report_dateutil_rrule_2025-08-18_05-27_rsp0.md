# Bug Report: dateutil.rrule Count Parameter Not Honored Near MAXYEAR

**Target**: `dateutil.rrule`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `rrule` class fails to generate the exact number of occurrences specified by the `count` parameter when the generated dates would exceed `datetime.MAXYEAR` (9999).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dateutil import rrule
import datetime

@given(
    freq=st.sampled_from([rrule.YEARLY, rrule.MONTHLY, rrule.WEEKLY, rrule.DAILY]),
    dtstart=st.datetimes(min_value=datetime.datetime(1900, 1, 1),
                         max_value=datetime.datetime(2100, 1, 1)),
    interval=st.integers(min_value=1, max_value=100),
    count=st.integers(min_value=1, max_value=100)
)
def test_count_property(freq, dtstart, interval, count):
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    assert len(events) == count, f"Expected {count} events but got {len(events)}"
```

**Failing input**: `freq=YEARLY, dtstart=datetime(2000, 1, 1), interval=87, count=93`

## Reproducing the Bug

```python
import datetime
from dateutil import rrule

freq = rrule.YEARLY
dtstart = datetime.datetime(2000, 1, 1, 0, 0)
interval = 87
count = 93

rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
events = list(rule)

print(f"Expected events: {count}")
print(f"Actual events: {len(events)}")
print(f"Last event year: {events[-1].year}")
print(f"Next would be year: {events[-1].year + interval}")
```

## Why This Is A Bug

The documentation for the `count` parameter states: "If given, this determines how many occurrences will be generated." There is no documented exception for dates exceeding `datetime.MAXYEAR`. When a user specifies `count=93`, they expect exactly 93 occurrences, not fewer due to an internal limitation. The current behavior silently truncates the results, violating the documented contract.

## Fix

```diff
--- a/dateutil/rrule.py
+++ b/dateutil/rrule.py
@@ -871,7 +871,10 @@ class rrule(rrulebase):
                         self._len = total
                         return
                     elif res >= self._dtstart:
                         if count is not None:
+                            total += 1
+                            yield res
                             count -= 1
                             if count < 0:
                                 self._len = total
                                 return
-                        total += 1
-                        yield res
+                        else:
+                            total += 1
+                            yield res
             else:
                 for i in dayset[start:end]:
@@ -889,11 +892,14 @@ class rrule(rrulebase):
                                 return
                             elif res >= self._dtstart:
                                 if count is not None:
+                                    total += 1
+                                    yield res
                                     count -= 1
                                     if count < 0:
                                         self._len = total
                                         return
-
-                                total += 1
-                                yield res
+                                else:
+                                    total += 1
+                                    yield res
 
             # Handle frequency and interval
             fixday = False
             if freq == YEARLY:
                 year += interval
                 if year > datetime.MAXYEAR:
+                    if count is not None and count > 0:
+                        # Count not satisfied, but can't generate more dates
+                        pass  # Could optionally raise an exception here
                     self._len = total
                     return
```

Note: A more comprehensive fix would require either:
1. Raising an exception when `count` cannot be satisfied due to MAXYEAR limits
2. Using a different date representation that can handle years > 9999
3. Clearly documenting this limitation in the `count` parameter description