# Bug Report: base64.b64encode Altchars Collision with Base64 Alphabet

**Target**: `base64.b64encode` and `base64.b64decode`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `base64.b64encode` and `base64.b64decode` functions fail to properly handle alternative characters (`altchars`) when those characters collide with the standard base64 alphabet, causing incorrect decoding and data corruption.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume

@given(st.binary(), st.binary(min_size=2, max_size=2))
def test_b64_altchars_round_trip(data, altchars):
    assume(b'+' not in altchars and b'/' not in altchars)
    assume(altchars[0] != altchars[1])
    encoded = base64.b64encode(data, altchars=altchars)
    decoded = base64.b64decode(encoded, altchars=altchars)
    assert decoded == data
```

**Failing input**: `data=b'\x000', altchars=b'\x00D'`

## Reproducing the Bug

```python
import base64

data = b'\x000'
altchars = b'\x00D'

encoded = base64.b64encode(data, altchars=altchars)
print(f"Encoded: {encoded!r}")  # b'ADA='

decoded = base64.b64decode(encoded, altchars=altchars)
print(f"Decoded: {decoded!r}")  # b'\x03\xf0'
print(f"Expected: {data!r}")     # b'\x000'
print(f"Data corrupted: {decoded != data}")  # True
```

## Why This Is A Bug

The `altchars` parameter is meant to replace only the '+' and '/' characters in base64 encoding. However, when the provided alternative characters collide with the standard base64 alphabet (A-Z, a-z, 0-9), the decode function incorrectly translates these alphabet characters back, corrupting the data.

In this case, 'D' is both:
1. Part of the standard base64 alphabet
2. Used as an alternative character for '/'

During decoding, ALL occurrences of 'D' in the encoded string are translated to '/', not just those that were originally '/'. This breaks the round-trip property that `decode(encode(x)) == x`.

## Fix

The issue lies in the unconditional translation during decoding. The functions should either:
1. Validate that `altchars` don't collide with the base64 alphabet
2. Use a different encoding scheme that tracks which characters were substituted

```diff
--- a/base64.py
+++ b/base64.py
@@ -51,6 +51,8 @@ def b64encode(s, altchars=None):
     encoded = binascii.b2a_base64(s, newline=False)
     if altchars is not None:
         assert len(altchars) == 2, repr(altchars)
+        if any(c in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=' for c in altchars):
+            raise ValueError("altchars cannot contain base64 alphabet characters")
         return encoded.translate(bytes.maketrans(b'+/', altchars))
     return encoded
```