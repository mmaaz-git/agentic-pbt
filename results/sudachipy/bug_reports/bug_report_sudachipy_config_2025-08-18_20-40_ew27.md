# Bug Report: sudachipy.config._filter_nulls Mutates Input Dictionary

**Target**: `sudachipy.config._filter_nulls`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_filter_nulls` function in sudachipy's config module mutates its input dictionary by deleting keys with None values, instead of returning a filtered copy.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from sudachipy import config

@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.text(), st.integers()),
    min_size=1, max_size=5
))
@example({"a": None, "b": "value"})
def test_filter_nulls_mutates_input_bug(data):
    original = data.copy()
    filtered = config._filter_nulls(data)
    
    if any(v is None for v in original.values()):
        assert data != original  # Input dictionary was mutated
        assert filtered is data  # Returns the same object
```

**Failing input**: `{"a": None, "b": "value"}`

## Reproducing the Bug

```python
from sudachipy import config

test_dict = {"keep": "value", "remove": None, "another": 42}
original = test_dict.copy()

result = config._filter_nulls(test_dict)

assert test_dict != original
assert "remove" not in test_dict
assert result is test_dict
```

## Why This Is A Bug

The function modifies its input argument in-place, which violates the principle of immutability for utility functions. This can lead to unexpected side effects when the same dictionary is used elsewhere in the code. Functions that filter data should typically return a new filtered copy rather than mutating the original.

## Fix

```diff
--- a/sudachipy/config.py
+++ b/sudachipy/config.py
@@ -73,9 +73,9 @@ class Config:
 
 
 def _filter_nulls(data: dict) -> dict:
-    keys = list(data.keys())
+    result = {}
     for key in keys:
         v = data[key]
-        if v is None:
-            del data[key]
-    return data
+        if v is not None:
+            result[key] = v
+    return result
```