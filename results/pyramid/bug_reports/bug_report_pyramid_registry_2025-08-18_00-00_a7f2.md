# Bug Report: pyramid.registry Introspectable.unrelate() Fails for Non-Existent Targets

**Target**: `pyramid.registry.Introspectable`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Introspectable.unrelate() stores unrelate operations that are later processed during registration. However, if the target introspectable doesn't exist when register() is called, it raises a KeyError instead of gracefully handling the missing target.

## Property-Based Test

```python
@given(
    cat1=st.text(min_size=1),
    disc1=st.text(min_size=1),
    cat2=st.text(min_size=1),
    disc2=st.text(min_size=1)
)
def test_introspectable_unrelate_before_relate(cat1, disc1, cat2, disc2):
    """Test that unrelate before relate doesn't cause issues"""
    assume((cat1, disc1) != (cat2, disc2))
    
    intr1 = pyramid.registry.Introspectable(cat1, disc1, "t1", "type1")
    intr1.unrelate(cat2, disc2)
    
    introspector = pyramid.registry.Introspector()
    intr1.register(introspector, None)  # Raises KeyError
```

**Failing input**: `cat1='0', disc1='0', cat2='0', disc2='1'`

## Reproducing the Bug

```python
import pyramid.registry

introspector = pyramid.registry.Introspector()
intr1 = pyramid.registry.Introspectable('cat1', 'disc1', 'title1', 'type1')
intr1.unrelate('cat2', 'disc2')
intr1.register(introspector, None)  # Raises KeyError: ('cat2', 'disc2')
```

## Why This Is A Bug

The unrelate() method allows specifying relationships to remove, but these are processed later during register(). If the target introspectable doesn't exist at registration time, the code raises a KeyError in `_get_intrs_by_pairs()`. This violates the principle that unrelating from a non-existent item should be a no-op, similar to how removing a non-existent key from a set doesn't raise an error.

## Fix

```diff
--- a/pyramid/registry.py
+++ b/pyramid/registry.py
@@ -191,11 +191,15 @@ class Introspector:
             L.append(y)
 
     def unrelate(self, *pairs):
-        introspectables = self._get_intrs_by_pairs(pairs)
-        relatable = ((x, y) for x in introspectables for y in introspectables)
-        for x, y in relatable:
-            L = self._refs.get(x, [])
-            if y in L:
-                L.remove(y)
+        try:
+            introspectables = self._get_intrs_by_pairs(pairs)
+            relatable = ((x, y) for x in introspectables for y in introspectables)
+            for x, y in relatable:
+                L = self._refs.get(x, [])
+                if y in L:
+                    L.remove(y)
+        except KeyError:
+            # Ignore unrelate operations for non-existent introspectables
+            pass
 
     def related(self, intr):
```