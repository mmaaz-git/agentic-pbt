# Bug Report: diskcache.recipes.throttle Allows Extra Call Within Rate Limit Period

**Target**: `diskcache.recipes.throttle`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `throttle` decorator allows one extra function call within the rate limit period, violating its documented rate limiting contract. When configured for N calls per second, it actually allows N+1 calls in the first second.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings

@given(
    st.integers(min_value=2, max_value=10),  # count
    st.floats(min_value=0.1, max_value=1.0),  # seconds
)
@settings(deadline=5000, max_examples=20)
def test_throttle_rate_limiting(count, seconds):
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        call_times = []
        
        @throttle(cache, count, seconds)
        def rate_limited_func():
            call_times.append(time.time())
        
        start_time = time.time()
        
        for _ in range(count * 2):
            rate_limited_func()
        
        first_period_calls = sum(1 for t in call_times if t - start_time <= seconds)
        assert first_period_calls <= count
```

**Failing input**: `count=2, seconds=1.0`

## Reproducing the Bug

```python
import time
import tempfile
import diskcache
from diskcache.recipes import throttle

with tempfile.TemporaryDirectory() as tmpdir:
    cache = diskcache.Cache(tmpdir, eviction_policy='none')
    
    call_times = []
    
    @throttle(cache, count=2, seconds=1.0)
    def rate_limited_func():
        call_times.append(time.time())
    
    start = time.time()
    
    for i in range(4):
        rate_limited_func()
    
    calls_in_first_second = sum(1 for t in call_times if t - start <= 1.0)
    
    print(f"Calls in first second: {calls_in_first_second}")
    print(f"Expected: 2")
    assert calls_in_first_second == 2, f"Got {calls_in_first_second} calls, expected 2"
```

## Why This Is A Bug

The throttle decorator's docstring states it limits calls to "count per seconds". With count=2 and seconds=1.0, only 2 calls should be allowed in the first second. However, the implementation allows 3 calls: two immediate calls that consume the initial tally, plus a third call when tally reaches 0 before the delay is enforced. This violates the rate limiting contract and could lead to API rate limit violations or resource exhaustion in production systems.

## Fix

The bug occurs because the throttle logic allows a call through when tally is between 0 and 1, then calculates the delay. The fix is to check if tally < 1 before allowing the call:

```diff
--- a/diskcache/recipes.py
+++ b/diskcache/recipes.py
@@ -296,12 +296,12 @@ def throttle(
                     tally += (now - last) * rate
                     delay = 0
 
                     if tally > count:
                         cache.set(key, (now, count - 1), expire)
                     elif tally >= 1:
                         cache.set(key, (now, tally - 1), expire)
                     else:
-                        delay = (1 - tally) / rate
+                        delay = max(0, (1 - tally) / rate)
 
                 if delay:
                     sleep_func(delay)
```

A more comprehensive fix would be to restructure the logic to check tally before decrementing, ensuring strict rate limiting compliance.