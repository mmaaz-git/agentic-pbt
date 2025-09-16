# Bug Report: fire.inspectutils Info() crashes on objects with failing __str__ methods

**Target**: `fire.inspectutils.Info` and `fire.inspectutils._InfoBackup`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `Info()` function crashes when called on objects whose `__str__()` method raises an exception, causing an unhandled exception instead of gracefully handling the error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.inspectutils as inspectutils

@st.composite  
def objects_with_failing_str(draw):
    exception_type = draw(st.sampled_from([ValueError, TypeError, RuntimeError]))
    message = draw(st.text(min_size=1, max_size=50))
    
    class BadStrObj:
        def __str__(self):
            raise exception_type(message)
    return BadStrObj()

@given(objects_with_failing_str())
def test_info_handles_bad_str(obj):
    """Info() should handle objects with failing __str__ without crashing."""
    info = inspectutils.Info(obj)  # This crashes!
    assert isinstance(info, dict)
    assert 'string_form' in info
```

**Failing input**: Any object with a `__str__()` method that raises an exception

## Reproducing the Bug

```python
import fire.inspectutils as inspectutils

class BadStr:
    def __str__(self):
        raise ValueError("Cannot convert to string!")

bad_obj = BadStr()
info = inspectutils.Info(bad_obj)
```

## Why This Is A Bug

The `Info()` function is meant to provide information about any Python component. It should handle all objects gracefully, even those with unusual behaviors. The function directly calls `str(component)` without exception handling at line 298 in `_InfoBackup()`, which causes a crash when the object's `__str__()` method raises an exception. This violates the expected behavior of a utility function that should be robust to various input types.

## Fix

```diff
--- a/fire/inspectutils.py
+++ b/fire/inspectutils.py
@@ -295,7 +295,11 @@ def _InfoBackup(component):
   info = {}
 
   info['type_name'] = type(component).__name__
-  info['string_form'] = str(component)
+  try:
+    info['string_form'] = str(component)
+  except Exception:
+    # If str() fails, use repr() or a fallback
+    info['string_form'] = f'<{type(component).__name__} object>'
 
   filename, lineno = GetFileAndLine(component)
   info['file'] = filename
```