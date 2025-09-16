# Bug Report: functools.wraps Fails When Decorating Classes

**Target**: `functools.wraps` and `functools.update_wrapper`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`functools.wraps` and `functools.update_wrapper` fail with an AttributeError when used to wrap classes, because class `__dict__` attributes are `mappingproxy` objects that lack the `update()` method.

## Property-Based Test

```python
import functools
from hypothesis import given, strategies as st


def test_wraps_with_class():
    """wraps should handle wrapping classes"""
    
    class OriginalClass:
        """Original class docstring"""
        pass
    
    @functools.wraps(OriginalClass)
    class WrapperClass:
        """Wrapper class docstring"""
        pass
    
    # Should have copied attributes
    assert WrapperClass.__doc__ == "Original class docstring"
    assert WrapperClass.__name__ == "OriginalClass"
    assert WrapperClass.__wrapped__ is OriginalClass
```

**Failing input**: Any attempt to use `@functools.wraps` on a class

## Reproducing the Bug

```python
import functools

class OriginalClass:
    """Original class documentation"""
    class_var = "test"

@functools.wraps(OriginalClass)
class WrapperClass:
    """Wrapper class documentation"""
    pass
```

Output:
```
AttributeError: 'mappingproxy' object has no attribute 'update'
```

## Why This Is A Bug

The bug occurs in `functools.py` at line 59:
```python
for attr in updated:
    getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
```

When `wrapper` is a class, `getattr(wrapper, '__dict__')` returns a `mappingproxy` object (read-only proxy to the class dictionary), which doesn't have an `update()` method. This makes `functools.wraps` unusable with classes, even though classes are callable objects that could reasonably be wrapped.

While the documentation refers to "wrapper function" and "wrapped function", Python classes are callable objects that can act as decorators and be decorated. The current implementation unnecessarily restricts this functionality.

## Fix

```diff
--- a/functools.py
+++ b/functools.py
@@ -56,7 +56,13 @@ def update_wrapper(wrapper,
         else:
             setattr(wrapper, attr, value)
     for attr in updated:
-        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
+        wrapper_attr = getattr(wrapper, attr)
+        wrapped_attr = getattr(wrapped, attr, {})
+        if hasattr(wrapper_attr, 'update'):
+            wrapper_attr.update(wrapped_attr)
+        else:
+            for key, value in wrapped_attr.items():
+                setattr(wrapper, key, value)
     # Issue #17482: set __wrapped__ last so we don't inadvertently copy it
     # from the wrapped function when updating __dict__
     wrapper.__wrapped__ = wrapped
```

This fix checks if the wrapper's attribute has an `update()` method. If not (as with class `mappingproxy` objects), it falls back to setting attributes individually.