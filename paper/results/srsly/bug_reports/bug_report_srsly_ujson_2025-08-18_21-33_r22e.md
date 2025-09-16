# Bug Report: srsly.ujson Converts Large Finite Floats to Infinity

**Target**: `srsly.ujson.dumps` / `srsly.ujson.loads`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

ujson incorrectly converts large but finite floating-point values to infinity during encoding/decoding, causing data corruption and making round-trip encoding impossible.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import srsly.ujson as ujson
import math

@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_finite_floats_remain_finite(f):
    """Finite floats should remain finite through encode/decode"""
    encoded = ujson.dumps(f)
    decoded = ujson.loads(encoded)
    assert math.isfinite(decoded), f"Finite float {f} became infinity"
    # Should be able to re-encode
    re_encoded = ujson.dumps(decoded)
```

**Failing input**: `1.7976931348623155e+308` (close to sys.float_info.max)

## Reproducing the Bug

```python
import srsly.ujson as ujson
import json

test_float = 1.7976931348623155e+308

# ujson converts to infinity
encoded = ujson.dumps(test_float)
decoded = ujson.loads(encoded)
print(f"Original: {test_float}")
print(f"Decoded: {decoded}")
print(f"Became infinity: {decoded == float('inf')}")

# Cannot re-encode infinity
try:
    ujson.dumps(decoded)
except OverflowError as e:
    print(f"Re-encode fails: {e}")

# Standard json preserves the value
json_encoded = json.dumps(test_float)
json_decoded = json.loads(json_encoded)
print(f"Standard json preserves: {json_decoded == test_float}")
```

## Why This Is A Bug

This is a critical data corruption bug. Finite floating-point values should never become infinity through JSON serialization. This violates the fundamental round-trip property that `loads(dumps(x)) == x` for valid JSON values. The bug makes it impossible to reliably serialize floating-point data near the maximum range, and the silent conversion to infinity can cause severe issues in numerical computations.

## Fix

```diff
--- a/srsly/ujson/lib/ultrajsonenc.c
+++ b/srsly/ujson/lib/ultrajsonenc.c
@@ -/* In the double encoding function */
-    // Current implementation likely has insufficient precision or overflow check
-    if (value > SOME_THRESHOLD) {
-        // Incorrectly converts to inf
-    }
+    // Proper handling of large floats
+    if (!isfinite(value)) {
+        // Handle actual infinity/NaN appropriately
+        return error;
+    }
+    // Use proper formatting with sufficient precision
+    // Ensure no overflow to infinity during conversion
```

The fix requires careful handling of floating-point limits in the C extension to ensure that finite values remain finite and are encoded with sufficient precision.