# Bug Report: diskcache Deque doesn't support slicing operations

**Target**: `diskcache.Deque.__getitem__`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `Deque` class inherits from `Sequence` but doesn't support slicing operations, resulting in a TypeError when attempting to slice a deque.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tempfile
from diskcache import Deque

@given(
    st.lists(st.integers(), min_size=5, max_size=20),
    st.integers(min_value=0, max_value=5),
    st.integers(min_value=0, max_value=5)
)
def test_deque_slicing(items, start, stop):
    """Test that Deque supports slicing operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deque = Deque(items, directory=tmpdir)
        
        # Adjust stop to be valid
        stop = min(start + stop, len(items))
        
        # Test slicing
        sliced = deque[start:stop]
        expected = items[start:stop]
        assert list(sliced) == expected
```

**Failing input**: `deque[0:1]` on any non-empty deque

## Reproducing the Bug

```python
import tempfile
from diskcache import Deque

with tempfile.TemporaryDirectory() as tmpdir:
    deque = Deque([1, 2, 3, 4, 5], directory=tmpdir)
    
    # This fails with: TypeError: '>=' not supported between instances of 'slice' and 'int'
    result = deque[1:3]
```

## Why This Is A Bug

The `Deque` class inherits from `collections.abc.Sequence` (line 49 in persistent.py: `class Deque(Sequence)`), which implies it should support all sequence operations including slicing. The Python documentation states that sequences should support slicing with `s[i:j]` notation. However, the current implementation only handles integer indices, not slice objects.

The `__getitem__` method passes the index directly to `_index()`, which assumes the index is an integer and tries to compare it with 0 at line 157, causing a TypeError when a slice object is passed.

## Fix

The `__getitem__` method needs to handle slice objects separately from integer indices:

```diff
--- a/diskcache/persistent.py
+++ b/diskcache/persistent.py
@@ -183,6 +183,8 @@ class Deque(Sequence):
 
     def __getitem__(self, index):
         """deque.__getitem__(index) <==> deque[index]
 
         Return corresponding item for `index` in deque.
 
@@ -201,7 +201,23 @@ class Deque(Sequence):
         :raises IndexError: if index out of range
 
         """
-        return self._index(index, self._cache.__getitem__)
+        if isinstance(index, slice):
+            # Handle slice objects
+            start, stop, step = index.indices(len(self))
+            if step != 1:
+                # For simplicity, only support step=1 initially
+                # Full implementation would need to handle arbitrary steps
+                result = []
+                for i in range(start, stop, step):
+                    result.append(self._index(i, self._cache.__getitem__))
+                return result
+            else:
+                result = []
+                for i in range(start, stop):
+                    result.append(self._index(i, self._cache.__getitem__))
+                return result
+        else:
+            # Handle integer index
+            return self._index(index, self._cache.__getitem__)
 
     def __setitem__(self, index, value):
         """deque.__setitem__(index, value) <==> deque[index] = value
```

Note: A complete fix would need to handle all slice cases properly and maintain consistency with the Sequence protocol.