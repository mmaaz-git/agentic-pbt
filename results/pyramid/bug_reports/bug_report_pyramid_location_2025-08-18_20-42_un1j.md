# Bug Report: pyramid.location AttributeError in inside() Function

**Target**: `pyramid.location.inside`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `inside()` function crashes with AttributeError when given objects that lack a `__parent__` attribute, while the related `lineage()` function handles this case gracefully.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.location import inside


class SimpleObject:
    def __init__(self, has_parent=True):
        if has_parent:
            self.__parent__ = None


@given(st.booleans())
def test_inside_handles_missing_parent_attr(has_parent):
    obj1 = SimpleObject(has_parent=has_parent)
    obj2 = SimpleObject(has_parent=True)
    
    # This should not raise AttributeError
    result = inside(obj1, obj2)
```

**Failing input**: `has_parent=False`

## Reproducing the Bug

```python
from pyramid.location import inside


class ObjectWithoutParent:
    pass


obj1 = ObjectWithoutParent()
obj2 = ObjectWithoutParent()

result = inside(obj1, obj2)  # Raises AttributeError
```

## Why This Is A Bug

The `inside()` function should handle objects without `__parent__` attributes gracefully, just like the `lineage()` function does in the same module. The `lineage()` function explicitly catches AttributeError when accessing `__parent__` (lines 64-67), but `inside()` does not. This inconsistency can cause unexpected crashes when using `inside()` with objects that don't follow the parent protocol.

## Fix

```diff
--- a/pyramid/location.py
+++ b/pyramid/location.py
@@ -25,7 +25,11 @@ def inside(resource1, resource2):
     while resource1 is not None:
         if resource1 is resource2:
             return True
-        resource1 = resource1.__parent__
+        try:
+            resource1 = resource1.__parent__
+        except AttributeError:
+            resource1 = None
+            break
 
     return False
```