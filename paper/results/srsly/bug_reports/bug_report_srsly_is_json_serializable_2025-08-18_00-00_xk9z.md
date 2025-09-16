# Bug Report: srsly.is_json_serializable Crashes with Non-UTF8 Bytes

**Target**: `srsly.is_json_serializable`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `is_json_serializable` function crashes with a UnicodeDecodeError when checking non-UTF8 byte strings, instead of returning False.

## Property-Based Test

```python
@given(st.builds(bytes, st.binary(min_size=1, max_size=100)))
@settings(max_examples=50)
def test_is_json_serializable_bytes(data):
    """Test that is_json_serializable handles bytes correctly"""
    result = srsly.is_json_serializable(data)
    # Should either return False or handle the bytes properly
    assert isinstance(result, bool)
```

**Failing input**: `b'\x80'`

## Reproducing the Bug

```python
import srsly

# This crashes with UnicodeDecodeError
result = srsly.is_json_serializable(b'\x80')
```

## Why This Is A Bug

The function `is_json_serializable` is supposed to check if an object is JSON-serializable and return a boolean. According to its docstring and implementation, it should catch exceptions and return False for non-serializable objects. However, it crashes with UnicodeDecodeError for certain byte strings instead of returning False.

## Fix

```diff
--- a/srsly/_json_api.py
+++ b/srsly/_json_api.py
@@ -186,7 +186,7 @@ def is_json_serializable(obj: Any) -> bool:
         # Check this separately here to prevent infinite recursions
         return False
     try:
         ujson.dumps(obj)
         return True
-    except (TypeError, OverflowError):
+    except (TypeError, OverflowError, UnicodeDecodeError):
         return False
```