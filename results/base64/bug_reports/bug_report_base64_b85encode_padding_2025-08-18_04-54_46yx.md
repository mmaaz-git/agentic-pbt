# Bug Report: base64.b85encode Padding Round-Trip Failure

**Target**: `base64.b85encode` with `pad=True` parameter
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `base64.b85encode` function with `pad=True` breaks the round-trip property, as `b85decode` cannot recover the original data length and returns padded data instead.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(st.binary())
def test_b85_padded_round_trip(data):
    encoded = base64.b85encode(data, pad=True)
    decoded = base64.b85decode(encoded)
    assert decoded == data
```

**Failing input**: `data=b'\x00'`

## Reproducing the Bug

```python
import base64

data = b'\x00'
print(f"Original: {data!r} (length {len(data)})")

encoded = base64.b85encode(data, pad=True)
print(f"Encoded: {encoded!r}")

decoded = base64.b85decode(encoded)
print(f"Decoded: {decoded!r} (length {len(decoded)})")
print(f"Expected: {data!r}")
print(f"Data changed: {decoded != data}")
```

## Why This Is A Bug

The documentation states that `pad=True` pads the input to a multiple of 4 bytes before encoding. However, this violates the fundamental expectation that encoding and decoding should be inverse operations.

The bug occurs because:
1. `b85encode(data, pad=True)` pads the input data with null bytes to reach a multiple of 4
2. `b85decode` has no way to know the original data length
3. The decoded result includes the padding bytes, changing the data

This makes `pad=True` effectively unusable for any data that isn't already a multiple of 4 bytes, as the round-trip property `decode(encode(x)) == x` is violated.

## Fix

Either:
1. Document that `pad=True` changes the data length and users must track original length separately
2. Encode the original length in the output (breaking change)
3. Deprecate the `pad` parameter as it doesn't provide the expected functionality

Option 1 (documentation fix):
```diff
--- a/base64.py
+++ b/base64.py
@@ -445,7 +445,9 @@ def b85encode(b, pad=False):
     """Encode bytes-like object b in base85 format and return a bytes object.
 
     If pad is true, the input is padded with b'\\0' so its length is a multiple of
-    4 bytes before encoding.
+    4 bytes before encoding. Note: When pad=True, the decoded output will include
+    the padding bytes. The original data length must be tracked separately if
+    the exact original data needs to be recovered.
     """
```