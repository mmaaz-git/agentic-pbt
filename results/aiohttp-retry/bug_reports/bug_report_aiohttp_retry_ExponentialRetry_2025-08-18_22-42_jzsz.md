# Bug Report: aiohttp_retry.ExponentialRetry Incorrect Timeout Calculation

**Target**: `aiohttp_retry.retry_options.ExponentialRetry`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

ExponentialRetry calculates incorrect timeout values because it receives 1-based attempt indices but expects 0-based, causing all retries to wait longer than intended.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import math
from aiohttp_retry.retry_options import ExponentialRetry

@given(
    start_timeout=st.floats(min_value=0.1, max_value=2.0),
    factor=st.floats(min_value=1.5, max_value=3.0)
)
def test_exponential_retry_incorrect_calculation(start_timeout, factor):
    """ExponentialRetry uses wrong exponents due to 1-based attempts"""
    retry = ExponentialRetry(
        attempts=3,
        start_timeout=start_timeout,
        factor=factor,
        max_timeout=100.0
    )
    
    # First retry (client.py passes attempt=1)
    timeout = retry.get_timeout(1)
    expected_for_first = start_timeout  # Should be start_timeout * factor^0
    actual = start_timeout * factor  # But gets start_timeout * factor^1
    assert math.isclose(timeout, actual, rel_tol=1e-9)
    # This shows first retry waits factor times longer than intended
```

**Failing input**: Any valid `start_timeout` and `factor` values demonstrate the issue

## Reproducing the Bug

```python
from aiohttp_retry.retry_options import ExponentialRetry

# Create ExponentialRetry with clear parameters
retry = ExponentialRetry(
    attempts=3,
    start_timeout=1.0,
    factor=2.0,
    max_timeout=100.0
)

# Expected behavior (0-based attempts):
# Attempt 0: 1.0 * 2^0 = 1.0 seconds
# Attempt 1: 1.0 * 2^1 = 2.0 seconds  
# Attempt 2: 1.0 * 2^2 = 4.0 seconds

# Actual behavior (1-based attempts from client.py):
print("Actual timeouts with 1-based attempts:")
for attempt in [1, 2, 3]:
    timeout = retry.get_timeout(attempt)
    print(f"Attempt {attempt}: {timeout} seconds (expected {1.0 * (2.0 ** (attempt-1))})")

# Output:
# Attempt 1: 2.0 seconds (expected 1.0)
# Attempt 2: 4.0 seconds (expected 2.0)
# Attempt 3: 8.0 seconds (expected 4.0)
```

## Why This Is A Bug

The retry logic in `client.py` passes `current_attempt` starting from 1 to `get_timeout()`. ExponentialRetry uses this directly as the exponent: `start_timeout * (factor ** attempt)`. This causes:
1. First retry waits `factor` times longer than intended
2. All subsequent retries also wait `factor` times longer
3. The intended exponential backoff pattern is shifted by one step

This also affects `JitterRetry` which inherits from `ExponentialRetry`.

## Fix

```diff
--- a/aiohttp_retry/retry_options.py
+++ b/aiohttp_retry/retry_options.py
@@ -74,7 +74,8 @@ class ExponentialRetry(RetryOptionsBase):
         response: ClientResponse | None = None,  # noqa: ARG002
     ) -> float:
         """Return timeout with exponential backoff."""
-        timeout = self._start_timeout * (self._factor**attempt)
+        # Convert 1-based attempt to 0-based for correct exponent
+        timeout = self._start_timeout * (self._factor**(attempt - 1 if attempt > 0 else 0))
         return min(timeout, self._max_timeout)
```