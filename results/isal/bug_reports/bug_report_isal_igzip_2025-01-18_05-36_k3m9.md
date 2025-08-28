# Bug Report: isal.igzip Missing Input Validation in compress() Function

**Target**: `isal.igzip.compress`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The `igzip.compress()` function lacks proper input validation for the `compresslevel` parameter, causing inconsistent error handling compared to `IGzipFile` and exposing underlying implementation errors instead of providing clear user feedback.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import isal.igzip as igzip
import isal.isal_zlib as isal_zlib

@given(
    st.binary(min_size=0, max_size=100),
    st.integers()
)
def test_invalid_compression_levels(data, level):
    """Test handling of invalid compression levels."""
    if not (isal_zlib.ISAL_BEST_SPEED <= level <= isal_zlib.ISAL_BEST_COMPRESSION):
        try:
            compressed = igzip.compress(data, compresslevel=level)
            decompressed = igzip.decompress(compressed)
            assert decompressed == data
        except (ValueError, TypeError):
            pass  # Expected behavior
    else:
        compressed = igzip.compress(data, compresslevel=level)
        decompressed = igzip.decompress(compressed)
        assert decompressed == data
```

**Failing input**: `data=b'', level=2147483648` and `data=b'', level=-1`

## Reproducing the Bug

```python
import isal.igzip as igzip

# Bug 1: OverflowError with large compression level
data = b''
level = 2147483648
compressed = igzip.compress(data, compresslevel=level)
# Raises: OverflowError: signed integer is greater than maximum

# Bug 2: IsalError with negative compression level
data = b''
level = -1
compressed = igzip.compress(data, compresslevel=level)
# Raises: igzip_lib.IsalError: Invalid memory level or compression level
```

## Why This Is A Bug

The `igzip.compress()` function fails to validate the `compresslevel` parameter before passing it to the underlying C library, causing:
1. **API Inconsistency**: `IGzipFile` properly validates compression levels and raises `ValueError` with a descriptive message, but `compress()` does not
2. **Poor Error Messages**: Users get cryptic `OverflowError` or `IsalError` messages instead of clear validation errors
3. **Contract Violation**: The function should validate inputs according to its documented range (0-3) before processing

## Fix

```diff
--- a/isal/igzip.py
+++ b/isal/igzip.py
@@ -224,6 +224,11 @@ def compress(data, compresslevel: int = _COMPRESS_LEVEL_BEST, *,
              mtime: Optional[SupportsInt] = None) -> bytes:
     """Compress data in one shot and return the compressed string.
     Optional argument is the compression level, in range of 0-3.
     """
+    if not (isal_zlib.ISAL_BEST_SPEED <= compresslevel
+            <= isal_zlib.ISAL_BEST_COMPRESSION):
+        raise ValueError(
+            f"Compression level should be between {isal_zlib.ISAL_BEST_SPEED} "
+            f"and {isal_zlib.ISAL_BEST_COMPRESSION}, got {compresslevel}."
+        )
     if mtime is None:
         mtime = time.time()
```