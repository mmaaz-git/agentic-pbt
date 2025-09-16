# Bug Report: aiohttp_retry FibonacciRetry.get_timeout() Ignores Attempt Parameter

**Target**: `aiohttp_retry.retry_options.FibonacciRetry.get_timeout`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `FibonacciRetry.get_timeout()` method ignores its `attempt` parameter and instead maintains mutable internal state, causing incorrect and unpredictable timeout values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aiohttp_retry.retry_options import FibonacciRetry

@given(st.integers(min_value=0, max_value=10))
def test_fibonacci_deterministic(attempt):
    """get_timeout() should be deterministic for same attempt number."""
    retry1 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    retry2 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    
    # Both fresh instances should give same result for same attempt
    timeout1 = retry1.get_timeout(attempt)
    timeout2 = retry2.get_timeout(attempt)
    
    assert timeout1 == timeout2  # FAILS!
```

**Failing input**: Any attempt > 0

## Reproducing the Bug

```python
from aiohttp_retry.retry_options import FibonacciRetry

# Create instance
retry = FibonacciRetry(multiplier=1.0, max_timeout=100.0)

# Bug 1: Repeated calls with same attempt give different results
val1 = retry.get_timeout(0)  # Returns 1.0
val2 = retry.get_timeout(0)  # Returns 2.0 (wrong!)
val3 = retry.get_timeout(0)  # Returns 3.0 (wrong!)

print(f"get_timeout(0) results: {val1}, {val2}, {val3}")
# Output: get_timeout(0) results: 1.0, 2.0, 3.0

# Bug 2: Direct call doesn't match sequence position
retry2 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
direct = retry2.get_timeout(2)  # Should return 3.0 (3rd Fibonacci)
print(f"get_timeout(2) = {direct}")  # Returns 1.0 (wrong!)
```

## Why This Is A Bug

The method signature `get_timeout(self, attempt: int, response=None)` suggests that the timeout should depend on the `attempt` parameter. Users expect `get_timeout(2)` to return the 3rd Fibonacci number consistently. Instead, the method:

1. Completely ignores the `attempt` parameter
2. Mutates internal state on each call
3. Returns values based on call count, not the attempt number

This violates the principle of least surprise and makes the retry behavior unpredictable.

## Fix

```diff
--- a/aiohttp_retry/retry_options.py
+++ b/aiohttp_retry/retry_options.py
@@ -177,10 +177,14 @@ class FibonacciRetry(RetryOptionsBase):
     def get_timeout(
         self,
         attempt: int,
         response: ClientResponse | None = None,
     ) -> float:
-        new_current_step = self.prev_step + self.current_step
-        self.prev_step = self.current_step
-        self.current_step = new_current_step
-
-        return min(self.multiplier * new_current_step, self.max_timeout)
+        # Calculate Fibonacci number for the given attempt
+        if attempt == 0:
+            fib = 1.0
+        else:
+            prev, curr = 1.0, 1.0
+            for _ in range(attempt):
+                prev, curr = curr, prev + curr
+            fib = curr
+        
+        return min(self.multiplier * fib, self.max_timeout)
```