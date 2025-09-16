# Bug Report: diskcache.persistent.Index Equality Comparison Crashes with Non-Mapping Types

**Target**: `diskcache.persistent.Index`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

Index.__eq__ and Index.__ne__ methods raise TypeError when comparing with non-mapping types like integers, None, or floats, instead of returning False/True respectively.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from diskcache.persistent import Index
import tempfile

non_mappings = st.one_of(
    st.integers(),
    st.floats(),
    st.none(),
    st.booleans(),
)

@given(
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=5),
    non_mappings
)
@settings(max_examples=100)
def test_index_equality_with_non_mappings(items, non_mapping):
    with tempfile.TemporaryDirectory() as tmpdir:
        index = Index(tmpdir, items)
        result_eq = (index == non_mapping)  # Should return False, but raises TypeError
        assert result_eq == False
```

**Failing input**: `items={'0': 0}, non_mapping=None`

## Reproducing the Bug

```python
from diskcache.persistent import Index
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    index = Index(tmpdir, {'0': 0})
    
    # This raises TypeError: object of type 'NoneType' has no len()
    result = (index == None)
    
    # This also raises TypeError: object of type 'int' has no len()
    result = (index == 123)
```

## Why This Is A Bug

The Python documentation states that equality comparisons should never raise exceptions. When comparing incompatible types, __eq__ should return False and __ne__ should return True. The current implementation violates this principle by attempting to call len() on arbitrary objects without type checking, causing crashes instead of returning appropriate boolean values.

## Fix

```diff
--- a/diskcache/persistent.py
+++ b/diskcache/persistent.py
@@ -1117,6 +1117,11 @@ class Index(MutableMapping):
         :return: True if index equals other
 
         """
+        # Check if other is a mapping-like object
+        try:
+            if not hasattr(other, '__getitem__'):
+                return False
+        except:
+            return False
         if len(self) != len(other):
             return False
 
@@ -1149,7 +1154,12 @@ class Index(MutableMapping):
         :return: True if index does not equal other
 
         """
-        return not self == other
+        try:
+            return not self == other
+        except (TypeError, AttributeError):
+            # If comparison fails, objects are not equal
+            return True
```