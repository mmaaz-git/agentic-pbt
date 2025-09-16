# Bug Report: lml_loader Remove Duplicates Fails on Unhashable Types

**Target**: `lml_loader.DataLoader.remove_duplicates`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `remove_duplicates` method crashes with a TypeError when given a list containing unhashable items like lists or dictionaries, because it attempts to add them to a set.

## Property-Based Test

```python
@given(st.lists(st.one_of(
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
)))
def test_remove_duplicates_unhashable(items):
    loader = DataLoader()
    deduped = loader.remove_duplicates(items)
    assert len(deduped) <= len(items)
```

**Failing input**: `items=[[]]` or `items=[{}]`

## Reproducing the Bug

```python
from lml_loader import DataLoader

loader = DataLoader()

# Test with lists
items = [[1, 2], [3, 4], [1, 2]]
try:
    result = loader.remove_duplicates(items)
except TypeError as e:
    print(f"Error with lists: {e}")

# Test with dicts
items = [{'a': 1}, {'b': 2}, {'a': 1}]
try:
    result = loader.remove_duplicates(items)
except TypeError as e:
    print(f"Error with dicts: {e}")
```

## Why This Is A Bug

The function claims to "remove duplicates while preserving order" but fails on valid Python lists containing unhashable items. Lists of lists and lists of dictionaries are common data structures that users would reasonably expect to deduplicate.

## Fix

```diff
--- a/lml_loader.py
+++ b/lml_loader.py
@@ -55,11 +55,20 @@ class DataLoader:
     def remove_duplicates(self, items: List) -> List:
         """Remove duplicates while preserving order."""
-        seen = set()
+        seen = set()
+        seen_unhashable = []
         result = []
         for item in items:
-            if item not in seen:
-                seen.add(item)
-                result.append(item)
+            try:
+                if item not in seen:
+                    seen.add(item)
+                    result.append(item)
+            except TypeError:
+                # Handle unhashable types
+                is_duplicate = any(item == seen_item for seen_item in seen_unhashable)
+                if not is_duplicate:
+                    seen_unhashable.append(item)
+                    result.append(item)
         return result
```