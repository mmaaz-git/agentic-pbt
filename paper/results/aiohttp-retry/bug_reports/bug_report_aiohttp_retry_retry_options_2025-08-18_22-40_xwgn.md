# Bug Report: FibonacciRetry Stateful get_timeout() Method

**Target**: `aiohttp_retry.retry_options.FibonacciRetry`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

FibonacciRetry.get_timeout() incorrectly maintains internal state between calls, causing the same attempt number to return different timeout values on subsequent calls.

## Property-Based Test

```python
@given(
    attempts=st.integers(min_value=1, max_value=10),
    multiplier=st.floats(min_value=0.5, max_value=2, allow_nan=False, allow_infinity=False),
    max_timeout=positive_floats(min_value=10, max_value=100)
)
def test_fibonacci_retry_statefulness_bug(attempts, multiplier, max_timeout):
    retry = FibonacciRetry(
        attempts=attempts,
        multiplier=multiplier,
        max_timeout=max_timeout
    )
    
    first_call = retry.get_timeout(0)
    second_call = retry.get_timeout(0)
    third_call = retry.get_timeout(0)
    
    assert first_call == second_call == third_call, \
        f"FibonacciRetry appears to be stateful! Calls produced: {first_call}, {second_call}, {third_call}"
```

**Failing input**: `attempts=1, multiplier=1.0, max_timeout=10.0`

## Reproducing the Bug

```python
from aiohttp_retry.retry_options import FibonacciRetry

retry = FibonacciRetry(attempts=5, multiplier=1.0, max_timeout=100.0)

print(f"First call:  {retry.get_timeout(0)}")  # Returns 2.0
print(f"Second call: {retry.get_timeout(0)}")  # Returns 3.0
print(f"Third call:  {retry.get_timeout(0)}")  # Returns 5.0
```

## Why This Is A Bug

The get_timeout() method should be idempotent for the same attempt number. When a retry mechanism queries the timeout for attempt 0 multiple times, it should always receive the same value. The current implementation updates internal state (self.prev_step and self.current_step) on every call, causing subsequent calls with the same attempt number to return different values. This violates the expected contract and could lead to unpredictable retry behavior in production systems.

## Fix

```diff
--- a/retry_options.py
+++ b/retry_options.py
@@ -151,10 +151,11 @@ class FibonacciRetry(RetryOptionsBase):
     def __init__(
         self,
         attempts: int = 3,
         multiplier: float = 1.0,
         statuses: Iterable[int] | None = None,
         exceptions: Iterable[type[Exception]] | None = None,
         methods: Iterable[str] | None = None,
         max_timeout: float = 3.0,
         retry_all_server_errors: bool = True,
         evaluate_response_callback: EvaluateResponseCallbackType | None = None,
     ) -> None:
         super().__init__(
             attempts=attempts,
             statuses=statuses,
             exceptions=exceptions,
             methods=methods,
             retry_all_server_errors=retry_all_server_errors,
             evaluate_response_callback=evaluate_response_callback,
         )
 
         self.max_timeout = max_timeout
         self.multiplier = multiplier
-        self.prev_step = 1.0
-        self.current_step = 1.0
 
     def get_timeout(
         self,
-        attempt: int,
+        attempt: int,
         response: ClientResponse | None = None,
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
+            fib = 1
+        else:
+            a, b = 1, 1
+            for _ in range(2, attempt + 1):
+                a, b = b, a + b
+            fib = b
+        
+        return min(self.multiplier * fib, self.max_timeout)
```