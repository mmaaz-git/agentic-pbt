# Bug Report: limits.safe_string UnicodeDecodeError on Non-UTF8 Bytes

**Target**: `limits.limits.safe_string`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `safe_string()` function crashes with UnicodeDecodeError when given bytes that are not valid UTF-8, despite claiming to normalize bytes to strings.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from limits.limits import safe_string

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.binary()
))
def test_safe_string_handles_all_types(value):
    result = safe_string(value)
    assert isinstance(result, str)
    if isinstance(value, bytes):
        assert result == value.decode()
    else:
        assert result == str(value)
```

**Failing input**: `b'\x80'`

## Reproducing the Bug

```python
from limits.limits import safe_string

result = safe_string(b'\x80')
```

## Why This Is A Bug

The docstring for `safe_string()` states it will "normalize a byte/str/int or float to a str", but it crashes on valid bytes input that isn't UTF-8 encoded. The function should handle arbitrary bytes gracefully, either by using error handling in decode() or by converting bytes to their string representation.

## Fix

```diff
--- a/limits/limits.py
+++ b/limits/limits.py
@@ -13,7 +13,7 @@ def safe_string(value: bytes | str | int | float) -> str:
     """
 
     if isinstance(value, bytes):
-        return value.decode()
+        return value.decode('utf-8', errors='replace')
 
     return str(value)
```