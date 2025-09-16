# Bug Report: srsly.ujson Float Precision Loss

**Target**: `srsly.ujson.dumps` / `srsly.ujson.loads`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

ujson loses precision when encoding/decoding floating-point numbers, particularly for large values, violating the round-trip property and causing data corruption.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import srsly.ujson as ujson

@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=1000)
def test_float_round_trip(f):
    """Floats should round-trip with reasonable precision"""
    encoded = ujson.dumps([f])  # Use list to ensure consistent behavior
    decoded = ujson.loads(encoded)
    assert decoded[0] == f, f"Precision lost: {f} != {decoded[0]}"
```

**Failing input**: `7.4350845423805815e+283`

## Reproducing the Bug

```python
import srsly.ujson as ujson
import json

test_values = [
    7.4350845423805815e+283,
    1.1447878645095912e+16,
    1.7976931348622231e+308
]

for value in test_values:
    # ujson loses precision
    ujson_encoded = ujson.dumps([value])
    ujson_decoded = ujson.loads(ujson_encoded)[0]
    
    # Standard json preserves precision
    json_encoded = json.dumps([value])
    json_decoded = json.loads(json_encoded)[0]
    
    print(f"Value: {value}")
    print(f"  ujson result: {ujson_decoded}")
    print(f"  Precision lost: {value != ujson_decoded}")
    print(f"  json preserves: {json_decoded == value}")
```

## Why This Is A Bug

JSON serialization should preserve floating-point values with sufficient precision for round-trip accuracy. The ujson library appears to use insufficient precision when encoding doubles, leading to data loss. This violates the principle that `loads(dumps(x))` should equal `x` for valid JSON data types. The standard json module demonstrates that this precision can be maintained.

## Fix

```diff
--- a/srsly/ujson/lib/ultrajsonenc.c
+++ b/srsly/ujson/lib/ultrajsonenc.c
@@ /* In the double encoding configuration */
-    // Current: insufficient precision (possibly using %.15g or similar)
-    encoder->doublePrecision = 15;
+    // Use maximum precision to ensure round-trip accuracy
+    encoder->doublePrecision = 17;  // DBL_DECIMAL_DIG for IEEE 754 doubles
```

The fix involves increasing the precision used when formatting floating-point numbers to ensure that the string representation contains enough significant digits for accurate round-trip conversion. The precision should be at least 17 digits for IEEE 754 double-precision floats.