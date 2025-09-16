# Bug Report: isal.isal_zlib Incompatible Compression Level Handling

**Target**: `isal.isal_zlib.compress`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The isal_zlib module fails to accept compression level -1, which is the standard default compression level in zlib, breaking compatibility with code expecting zlib-compatible behavior.

## Property-Based Test

```python
@given(data=st.binary(min_size=0, max_size=10000))
@settings(max_examples=500)
def test_extreme_compression_levels(data):
    """Test boundary compression levels"""
    for level in [-1, 0, 3, 4]:  # -1 should be default, 4 should be clamped to 3
        try:
            compressed = isal_zlib.compress(data, level=level)
            decompressed = isal_zlib.decompress(compressed)
            assert decompressed == data
        except ValueError:
            # Level 4 might raise an error, which is fine
            pass
```

**Failing input**: `data=b''` (or any data), `level=-1`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.isal_zlib as isal_zlib
import zlib

data = b"Hello, World!"

# Standard zlib accepts -1 as default compression level
zlib_compressed = zlib.compress(data, level=-1)

# isal_zlib fails with the same level
try:
    isal_compressed = isal_zlib.compress(data, level=-1)
except Exception as e:
    print(f"isal_zlib fails: {e}")

# Also, the constants are incompatible
print(f"zlib.Z_DEFAULT_COMPRESSION = {zlib.Z_DEFAULT_COMPRESSION}")
print(f"isal_zlib.Z_DEFAULT_COMPRESSION = {isal_zlib.Z_DEFAULT_COMPRESSION}")
```

## Why This Is A Bug

This violates the expected behavior of a zlib-compatible library. The isal_zlib module presents itself as a drop-in replacement for zlib, but:

1. It rejects compression level -1, which is the standard default in zlib
2. It redefines Z_DEFAULT_COMPRESSION to be 2 instead of -1
3. Code that uses `compress(data, level=-1)` or `compress(data, level=zlib.Z_DEFAULT_COMPRESSION)` will fail when switching from zlib to isal_zlib

This breaks the API contract and prevents isal_zlib from being a true drop-in replacement for zlib.

## Fix

The module should accept -1 as a valid compression level and map it internally to the appropriate ISA-L default level:

```diff
--- a/isal_zlib.c
+++ b/isal_zlib.c
@@ function compress(data, level=2, wbits=15):
+    # Map zlib-compatible -1 to ISA-L default
+    if level == -1:
+        level = 2  # or ISAL_DEFAULT_COMPRESSION
     if level < 0 or level > 3:
         raise IsalError("Invalid memory level or compression level")
     # ... rest of compression logic
```

Additionally, Z_DEFAULT_COMPRESSION should be defined as -1 for compatibility with standard zlib.