# Bug Report: cryptography.hazmat.primitives.keywrap Empty Key Wrap Round-Trip Failure

**Target**: `cryptography.hazmat.primitives.keywrap.aes_key_wrap_with_padding`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `aes_key_wrap_with_padding` function produces invalid output when wrapping an empty key, which cannot be unwrapped by `aes_key_unwrap_with_padding`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from cryptography.hazmat.primitives import keywrap

@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32)
)
def test_aes_key_wrap_empty_with_padding(wrapping_key):
    """Empty key should be wrappable and unwrappable with padding"""
    empty_key = b""
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, empty_key)
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    assert unwrapped == empty_key
```

**Failing input**: `wrapping_key=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'`

## Reproducing the Bug

```python
from cryptography.hazmat.primitives import keywrap

wrapping_key = b'\x00' * 16
empty_key = b""

wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, empty_key)
print(f"Wrapped: {wrapped.hex()} ({len(wrapped)} bytes)")

unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
```

## Why This Is A Bug

The AES key wrap with padding specification (RFC 5649) should support wrapping keys of any length, including empty keys. The round-trip property (wrap then unwrap should return the original key) is fundamental to the correctness of the algorithm. When wrapping an empty key, the function returns only 8 bytes (the AIV), but the unwrap function requires at least 16 bytes, causing an InvalidUnwrap exception with message "Must be at least 16 bytes".

## Fix

```diff
--- a/cryptography/hazmat/primitives/keywrap.py
+++ b/cryptography/hazmat/primitives/keywrap.py
@@ -92,7 +92,7 @@ def aes_key_wrap_with_padding(
     # pad the key to wrap if necessary
     pad = (8 - (len(key_to_wrap) % 8)) % 8
     key_to_wrap = key_to_wrap + b"\x00" * pad
-    if len(key_to_wrap) == 8:
+    if len(key_to_wrap) == 8 or len(key_to_wrap) == 0:
         # RFC 5649 - 4.1 - exactly 8 octets after padding
         encryptor = Cipher(AES(wrapping_key), ECB()).encryptor()
         b = encryptor.update(aiv + key_to_wrap)
```

However, this fix alone is incomplete. The proper fix requires handling the empty key case specially to ensure the output is at least 16 bytes, matching the unwrap function's requirements.