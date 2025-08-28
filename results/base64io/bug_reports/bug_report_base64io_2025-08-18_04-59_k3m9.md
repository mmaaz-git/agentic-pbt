# Bug Report: base64io.Base64IO write() returns incorrect byte count

**Target**: `base64io.Base64IO.write()`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `write()` method violates the standard IO contract by returning the number of base64-encoded bytes written to the underlying stream instead of the number of user bytes written.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import base64io
import io

@given(st.binary(min_size=1))
def test_write_return_value_semantics(data):
    """Test that write() returns the number of bytes written from user perspective."""
    buffer = io.BytesIO()
    
    with base64io.Base64IO(buffer) as b64:
        bytes_written = b64.write(data)
        
        # The return value should be the number of user bytes written,
        # not the number of encoded bytes written to the underlying stream
        assert bytes_written == len(data), \
            f"write() returned {bytes_written} but wrote {len(data)} user bytes"
```

**Failing input**: `b'\x00'`

## Reproducing the Bug

```python
import io
import base64io

buffer = io.BytesIO()
with base64io.Base64IO(buffer) as b64:
    data = b'\x00'
    bytes_written = b64.write(data)
    print(f"Data length: {len(data)}")
    print(f"write() returned: {bytes_written}")
    assert bytes_written == len(data), f"Expected {len(data)}, got {bytes_written}"
```

## Why This Is A Bug

The Python IO specification requires that `write()` returns the number of bytes written from the caller's perspective. The current implementation returns the number of base64-encoded bytes written to the underlying stream, which is incorrect. This violates the `io.IOBase.write()` contract and can break code that relies on the return value to track write progress.

## Fix

```diff
--- a/base64io/__init__.py
+++ b/base64io/__init__.py
@@ -205,10 +205,11 @@ class Base64IO(io.IOBase):
 
         # If an even base64 chunk or finalizing the stream, write through.
         if len(_bytes_to_write) % 3 == 0:
-            return self.__wrapped.write(base64.b64encode(_bytes_to_write))
+            self.__wrapped.write(base64.b64encode(_bytes_to_write))
+            return len(b)
 
         # We're not finalizing the stream, so stash the trailing bytes and encode the rest.
         trailing_byte_pos = -1 * (len(_bytes_to_write) % 3)
         self.__write_buffer = _bytes_to_write[trailing_byte_pos:]
-        return self.__wrapped.write(base64.b64encode(_bytes_to_write[:trailing_byte_pos]))
+        self.__wrapped.write(base64.b64encode(_bytes_to_write[:trailing_byte_pos]))
+        return len(b)
```