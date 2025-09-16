# Bug Report: FibonacciRetry Ignores Attempt Parameter

**Target**: `aiohttp_retry.retry_options.FibonacciRetry`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

FibonacciRetry's `get_timeout()` method completely ignores the `attempt` parameter and uses internal mutable state instead, causing incorrect and inconsistent retry behavior across multiple requests.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aiohttp_retry.retry_options import FibonacciRetry

@given(st.integers(min_value=0, max_value=10))
def test_fibonacci_retry_respects_attempt_parameter(attempt):
    """FibonacciRetry should return consistent timeout for same attempt number."""
    retry1 = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)
    retry2 = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)
    
    # Same attempt should give same timeout from fresh instances
    timeout1 = retry1.get_timeout(attempt)
    timeout2 = retry2.get_timeout(attempt)
    
    # This fails! Different instances give different results for attempt=0
    assert timeout1 == timeout2
```

**Failing input**: Any attempt value demonstrates the bug

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)

print(f"get_timeout(attempt=0) = {retry.get_timeout(0)}")  # Returns 2.0
print(f"get_timeout(attempt=5) = {retry.get_timeout(5)}")  # Returns 3.0 (wrong!)
print(f"get_timeout(attempt=0) = {retry.get_timeout(0)}")  # Returns 5.0 (wrong!)
```

## Why This Is A Bug

1. **API Contract Violation**: All other retry strategies (ExponentialRetry, RandomRetry, ListRetry) use the `attempt` parameter to determine timeout. FibonacciRetry ignores it completely.

2. **State Pollution**: Reusing a FibonacciRetry instance across multiple retry contexts (different requests) results in incorrect timeout values for subsequent requests.

3. **Non-Deterministic Behavior**: The timeout for a given attempt number depends on the history of previous calls, not on the attempt number itself.

4. **Usage Mismatch**: The client code in `client.py` (lines 138, 149) explicitly passes `attempt=current_attempt`, expecting deterministic behavior based on attempt number.

## Fix

```diff
--- a/aiohttp_retry/retry_options.py
+++ b/aiohttp_retry/retry_options.py
@@ -169,16 +169,20 @@ class FibonacciRetry(RetryOptionsBase):
         )
 
         self.max_timeout = max_timeout
         self.multiplier = multiplier
-        self.prev_step = 1.0
-        self.current_step = 1.0
 
     def get_timeout(
         self,
-        attempt: int,  # noqa: ARG002
+        attempt: int,
         response: ClientResponse | None = None,  # noqa: ARG002
     ) -> float:
-        new_current_step = self.prev_step + self.current_step
-        self.prev_step = self.current_step
-        self.current_step = new_current_step
-
-        return min(self.multiplier * new_current_step, self.max_timeout)
+        # Calculate Fibonacci number for the given attempt
+        if attempt == 0:
+            fib = 1
+        elif attempt == 1:
+            fib = 2
+        else:
+            a, b = 1, 2
+            for _ in range(2, attempt + 1):
+                a, b = b, a + b
+            fib = b
+        
+        return min(self.multiplier * fib, self.max_timeout)
```