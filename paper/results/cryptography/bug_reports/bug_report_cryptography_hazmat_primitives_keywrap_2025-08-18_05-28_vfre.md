# Bug Report: cryptography.hazmat.primitives.keywrap Invalid Exception Type on Malformed Input

**Target**: `cryptography.hazmat.primitives.keywrap.aes_key_unwrap_with_padding`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `aes_key_unwrap_with_padding` function raises `ValueError` instead of `InvalidUnwrap` when given wrapped keys that are not multiples of 8 bytes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from cryptography.hazmat.primitives import keywrap
from cryptography.hazmat.primitives.keywrap import InvalidUnwrap

@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(min_size=17, max_size=100).filter(lambda x: len(x) % 8 != 0)
)
def test_aes_key_unwrap_with_padding_invalid_length_exception(wrapping_key, wrapped_key):
    """Invalid wrapped key lengths should raise InvalidUnwrap, not ValueError"""
    with pytest.raises(InvalidUnwrap):
        keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)
```

**Failing input**: `wrapping_key=b'\x00' * 16, wrapped_key=b'\x00' * 17`

## Reproducing the Bug

```python
from cryptography.hazmat.primitives import keywrap

wrapping_key = b'\x00' * 16
wrapped_key = b'\x00' * 17

try:
    keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)
except keywrap.InvalidUnwrap:
    print("Got expected InvalidUnwrap")
except ValueError as e:
    print(f"Got unexpected ValueError: {e}")
```

## Why This Is A Bug

The function's API contract should raise `InvalidUnwrap` for all invalid wrapped key inputs to maintain consistent error handling. Currently, when the wrapped key length is > 16 bytes but not a multiple of 8, the function incorrectly raises `ValueError` with message "The length of the provided data is not a multiple of the block length" instead of the expected `InvalidUnwrap` exception. This inconsistency makes error handling difficult for users of the API.

## Fix

```diff
--- a/cryptography/hazmat/primitives/keywrap.py
+++ b/cryptography/hazmat/primitives/keywrap.py
@@ -123,6 +123,9 @@ def aes_key_unwrap_with_padding(
         data = out[8:]
         n = 1
     else:
+        if len(wrapped_key) % 8 != 0:
+            raise InvalidUnwrap("The wrapped key must be a multiple of 8 bytes")
+        
         r = [wrapped_key[i : i + 8] for i in range(0, len(wrapped_key), 8)]
         encrypted_aiv = r.pop(0)
         n = len(r)
```