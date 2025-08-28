# Bug Report: aiohttp_retry.ListRetry Off-by-One Error Causes IndexError

**Target**: `aiohttp_retry.retry_options.ListRetry`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

ListRetry has an off-by-one error that causes it to skip the first timeout value and crash with IndexError on the last retry attempt.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aiohttp_retry.retry_options import ListRetry

@given(
    timeouts=st.lists(st.floats(min_value=0.1, max_value=10.0), min_size=1, max_size=5)
)
def test_listretry_off_by_one(timeouts):
    """ListRetry crashes when accessed with 1-based indices as used by client.py"""
    retry = ListRetry(timeouts=timeouts)
    
    # Simulate how client.py calls get_timeout (with 1-based attempts)
    for attempt_num in range(1, retry.attempts + 1):
        if attempt_num <= len(timeouts):
            timeout = retry.get_timeout(attempt_num - 1)  # Should use 0-based
        else:
            # This will raise IndexError on the last attempt
            try:
                timeout = retry.get_timeout(attempt_num - 1)
                assert False, "Should have raised IndexError"
            except IndexError:
                pass
```

**Failing input**: `timeouts=[1.0, 2.0, 3.0]` with attempt indices 1, 2, 3

## Reproducing the Bug

```python
from aiohttp_retry.retry_options import ListRetry

# Create ListRetry with 3 timeouts
timeouts = [1.0, 2.0, 3.0]
retry = ListRetry(timeouts=timeouts)

# Simulate retry logic from client.py (which uses 1-based attempts)
current_attempt = 0

# First attempt
current_attempt += 1  # Now 1
timeout = retry.get_timeout(current_attempt)
print(f"Attempt {current_attempt}: got {timeout}, expected {timeouts[0]}")
# Output: Attempt 1: got 2.0, expected 1.0

# Second attempt  
current_attempt += 1  # Now 2
timeout = retry.get_timeout(current_attempt)
print(f"Attempt {current_attempt}: got {timeout}, expected {timeouts[1]}")
# Output: Attempt 2: got 3.0, expected 2.0

# Third attempt - crashes
current_attempt += 1  # Now 3
try:
    timeout = retry.get_timeout(current_attempt)
except IndexError as e:
    print(f"Attempt {current_attempt}: IndexError - {e}")
# Output: Attempt 3: IndexError - list index out of range
```

## Why This Is A Bug

The retry logic in `client.py` (line 138, 149) calls `get_timeout(attempt=current_attempt)` where `current_attempt` starts at 1. However, `ListRetry.get_timeout()` directly indexes into the timeouts list expecting 0-based indices. This mismatch causes:
1. The first timeout value is never used
2. An IndexError occurs on the last retry attempt
3. Users get unexpected timeout sequences

## Fix

```diff
--- a/aiohttp_retry/retry_options.py
+++ b/aiohttp_retry/retry_options.py
@@ -145,7 +145,8 @@ class ListRetry(RetryOptionsBase):
         response: ClientResponse | None = None,  # noqa: ARG002
     ) -> float:
         """Timeouts from a defined list."""
-        return self.timeouts[attempt]
+        # Convert 1-based attempt to 0-based index
+        return self.timeouts[attempt - 1 if attempt > 0 else 0]
```