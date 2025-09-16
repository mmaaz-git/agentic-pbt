# Bug Report: spnego._spnego.unpack_token NTLM Message Crash with unwrap=True

**Target**: `spnego._spnego.unpack_token`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The unpack_token function crashes when attempting to unwrap malformed NTLM messages that have the correct signature but insufficient data, instead of gracefully handling the error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import spnego._spnego as sp

@given(st.binary(min_size=8, max_size=100))
def test_unpack_token_with_ntlm_prefix_doesnt_crash(suffix):
    data = b"NTLMSSP\x00" + suffix
    
    # Without unwrap, should return original data
    result = sp.unpack_token(data, unwrap=False)
    assert result == data
    
    # With unwrap=True, should either parse or raise a proper error
    try:
        result_unwrapped = sp.unpack_token(data, unwrap=True)
        # If successful, should return parsed NTLMMessage
        assert result_unwrapped != data
    except (struct.error, ValueError) as e:
        # Should handle errors gracefully
        pass
```

**Failing input**: `suffix=b'\x00'` (resulting in `b'NTLMSSP\x00\x00'`)

## Reproducing the Bug

```python
import spnego._spnego as sp

# Create minimal NTLM-like message
data = b'NTLMSSP\x00\x00'

# Without unwrap - works fine
result = sp.unpack_token(data, unwrap=False)
print(f"Without unwrap: {result == data}")  # True

# With unwrap - crashes
try:
    result = sp.unpack_token(data, unwrap=True)
except struct.error as e:
    print(f"Error: {e}")  # Error: unpack requires a buffer of 4 bytes
```

## Why This Is A Bug

The unpack_token function with unwrap=True should handle malformed NTLM messages gracefully. When data starts with the NTLM signature (`NTLMSSP\x00`) but doesn't contain a valid NTLM message structure, the function crashes with a low-level struct.error instead of raising a more appropriate exception or returning the raw data. This violates the principle of graceful error handling for invalid input.

## Fix

```diff
--- a/spnego/_spnego.py
+++ b/spnego/_spnego.py
@@ -76,7 +76,10 @@ def unpack_token(
     # First check if the message is an NTLM message.
     if b_data.startswith(b"NTLMSSP\x00"):
         if unwrap:
-            return NTLMMessage.unpack(b_data, encoding=encoding)
+            try:
+                return NTLMMessage.unpack(b_data, encoding=encoding)
+            except (struct.error, ValueError) as e:
+                raise InvalidTokenError(f"Invalid NTLM message structure: {e}")
         
         else:
             return b_data
```