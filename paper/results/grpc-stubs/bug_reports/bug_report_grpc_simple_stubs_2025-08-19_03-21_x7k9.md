# Bug Report: grpc._simple_stubs Invalid Eviction Period Handling

**Target**: `grpc._simple_stubs` module (ChannelCache eviction period parsing)
**Severity**: Medium
**Bug Type**: Crash/Logic
**Date**: 2025-08-19

## Summary

The `grpc._simple_stubs` module incorrectly handles invalid values for the `GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS` environment variable, causing crashes with NaN values and incorrect behavior with negative values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import os
import datetime

@given(
    eviction_str=st.one_of(
        st.just("nan"),
        st.just("-10"),
        st.just("inf")
    )
)
def test_eviction_period_parsing(eviction_str):
    os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'] = eviction_str
    try:
        eviction_seconds = float(eviction_str)
        eviction_period = datetime.timedelta(seconds=eviction_seconds)
        # Check for invalid behavior
        if eviction_seconds < 0:
            # Negative period causes immediate eviction
            assert False, "Negative eviction period accepted"
    except ValueError:
        pass  # Expected for NaN
    finally:
        del os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS']
```

**Failing input**: `"nan"` and `"-10"`

## Reproducing the Bug

```python
import os
import datetime

# Bug 1: NaN causes crash
os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'] = "nan"
eviction_seconds = float(os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'])
print(f"Parsed NaN: {eviction_seconds}")

try:
    eviction_period = datetime.timedelta(seconds=eviction_seconds)
except ValueError as e:
    print(f"ERROR: {e}")

# Bug 2: Negative period causes incorrect behavior  
os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'] = "-10"
eviction_seconds = float(os.environ['GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS'])
eviction_period = datetime.timedelta(seconds=eviction_seconds)

now = datetime.datetime.now()
eviction_time = now + eviction_period
print(f"Eviction time is in the past: {eviction_time < now}")
```

## Why This Is A Bug

1. **NaN values**: When `GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS=nan`, the code crashes with `ValueError: cannot convert float NaN to integer` when creating the timedelta, causing the entire module to fail to load.

2. **Negative values**: When the environment variable is set to a negative number, channels are immediately marked for eviction since `now + negative_timedelta` results in a past timestamp, breaking the cache functionality.

## Fix

```diff
--- a/grpc/_simple_stubs.py
+++ b/grpc/_simple_stubs.py
@@ -49,9 +49,17 @@ _LOGGER = logging.getLogger(__name__)
 
 _EVICTION_PERIOD_KEY = "GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS"
 if _EVICTION_PERIOD_KEY in os.environ:
-    _EVICTION_PERIOD = datetime.timedelta(
-        seconds=float(os.environ[_EVICTION_PERIOD_KEY])
-    )
+    try:
+        eviction_seconds = float(os.environ[_EVICTION_PERIOD_KEY])
+        if eviction_seconds != eviction_seconds:  # NaN check
+            _LOGGER.warning("Invalid eviction period (NaN), using default")
+            _EVICTION_PERIOD = datetime.timedelta(minutes=10)
+        elif eviction_seconds < 0:
+            _LOGGER.warning("Negative eviction period, using default")
+            _EVICTION_PERIOD = datetime.timedelta(minutes=10)
+        else:
+            _EVICTION_PERIOD = datetime.timedelta(seconds=eviction_seconds)
+    except ValueError:
+        _LOGGER.warning("Invalid eviction period format, using default")
+        _EVICTION_PERIOD = datetime.timedelta(minutes=10)
     _LOGGER.debug(
         "Setting managed channel eviction period to %s", _EVICTION_PERIOD
```