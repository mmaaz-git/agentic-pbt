# Bug Report: tqdm.std.EMA ZeroDivisionError with smoothing=0

**Target**: `tqdm.std.EMA`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The EMA class raises a ZeroDivisionError when initialized with smoothing=0.0 and called with any value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tqdm.std import EMA

@given(
    smoothing=st.floats(min_value=0, max_value=1, allow_nan=False),
    values=st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False), min_size=1, max_size=100)
)
def test_ema_bounds(smoothing, values):
    ema = EMA(smoothing=smoothing)
    for val in values:
        result = ema(val)
    min_val = min(values)
    max_val = max(values)
    assert min_val - 1e-10 <= result <= max_val + 1e-10
```

**Failing input**: `smoothing=0.0, values=[0.0]`

## Reproducing the Bug

```python
from tqdm.std import EMA

ema = EMA(smoothing=0.0)
result = ema(1.0)  # ZeroDivisionError: float division by zero
```

## Why This Is A Bug

The EMA class documentation states that smoothing ranges from 0 to 1, where 0 yields the old value. However, when smoothing=0 (alpha=0, beta=1), the denominator `(1 - beta ** self.calls)` becomes zero after the first call, causing a division by zero error. This violates the documented behavior that smoothing=0 should yield the old value.

## Fix

```diff
--- a/tqdm/std.py
+++ b/tqdm/std.py
@@ -239,7 +239,10 @@ class EMA(object):
         if x is not None:
             self.last = self.alpha * x + beta * self.last
             self.calls += 1
-        return self.last / (1 - beta ** self.calls) if self.calls else self.last
+        if self.calls == 0:
+            return self.last
+        denominator = 1 - beta ** self.calls
+        return self.last if denominator == 0 else self.last / denominator
```