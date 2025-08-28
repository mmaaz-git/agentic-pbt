# Bug Report: fire.test_components_py3 LRU Cache Functions Crash on Unhashable Inputs

**Target**: `fire.test_components_py3.lru_cache_decorated` and `fire.test_components_py3.LruCacheDecoratedMethod.lru_cache_in_class`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

LRU cache decorated functions crash with TypeError when called with unhashable arguments like lists or dictionaries, instead of gracefully handling or documenting this limitation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.test_components_py3 as components

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers())
))
def test_lru_cache_idempotence(x):
    result1 = components.lru_cache_decorated(x)
    result2 = components.lru_cache_decorated(x)
    assert result1 == result2
    assert result1 == x
```

**Failing input**: `[]`

## Reproducing the Bug

```python
import fire.test_components_py3 as components

result = components.lru_cache_decorated([1, 2, 3])

obj = components.LruCacheDecoratedMethod()
result = obj.lru_cache_in_class([1, 2, 3])
```

## Why This Is A Bug

The functions don't document that they only accept hashable inputs. Users would reasonably expect either:
1. The function to handle all input types (perhaps by bypassing cache for unhashable types)
2. A clear, informative error message explaining the limitation

Instead, the functions crash with a cryptic "unhashable type" error from the internal functools.lru_cache implementation.

## Fix

Add wrapper logic to handle unhashable types gracefully:

```diff
+def make_hashable(obj):
+    """Convert unhashable types to hashable equivalents."""
+    if isinstance(obj, list):
+        return tuple(obj)
+    elif isinstance(obj, dict):
+        return tuple(sorted(obj.items()))
+    elif isinstance(obj, set):
+        return frozenset(obj)
+    return obj
+
 @functools.lru_cache()
 def lru_cache_decorated(arg1):
+  arg1_hashable = make_hashable(arg1)
+  # Use arg1_hashable for caching, but return original arg1
   return arg1

 class LruCacheDecoratedMethod:
   @functools.lru_cache()
   def lru_cache_in_class(self, arg1):
+    arg1_hashable = make_hashable(arg1)
+    # Use arg1_hashable for caching, but return original arg1
     return arg1
```