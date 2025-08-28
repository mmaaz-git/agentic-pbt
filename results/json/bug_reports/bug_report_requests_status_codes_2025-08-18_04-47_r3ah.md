# Bug Report: requests.status_codes LookupDict Attribute Access Inconsistency

**Target**: `requests.status_codes`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `LookupDict` class in `requests.structures` has inconsistent behavior between attribute access and dictionary-style access for inherited dict methods, violating the expected contract that `obj.attr` should equal `obj["attr"]` for dict-like objects.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.status_codes as sc

@given(st.sampled_from(['items', 'keys', 'values', 'update', 'clear', 'get', 'pop', 'setdefault']))
def test_lookupdict_dict_methods_access(method_name):
    """Dict methods accessed through __getitem__ should not be None if they exist as methods."""
    has_method = hasattr(sc.codes, method_name) and callable(getattr(sc.codes, method_name))
    item_value = sc.codes[method_name]
    
    if has_method:
        assert item_value is not None, f"Method {method_name} exists but __getitem__ returns None"
```

**Failing input**: `method_name='items'`

## Reproducing the Bug

```python
import requests.status_codes as sc

# Dict method exists as attribute
assert hasattr(sc.codes, 'items')
assert callable(sc.codes.items)

# But returns None via __getitem__
assert sc.codes['items'] is None

# This violates expected dict-like behavior
print(f"codes.items = {sc.codes.items}")
print(f"codes['items'] = {sc.codes['items']}")
assert sc.codes.items != sc.codes['items']
```

## Why This Is A Bug

The `LookupDict` class inherits from `dict` but overrides `__getitem__` to look only in `self.__dict__`, ignoring inherited methods. This creates an inconsistency where:

1. `codes.items` returns the dict method (via normal attribute resolution)
2. `codes["items"]` returns `None` (via the custom `__getitem__`)

This violates the principle of least surprise for dict-like objects and can cause silent failures when users dynamically access attributes using string keys.

## Fix

```diff
--- a/requests/structures.py
+++ b/requests/structures.py
@@ -92,7 +92,11 @@ class LookupDict(dict):
 
     def __getitem__(self, key):
         # We allow fall-through here, so values default to None
-
-        return self.__dict__.get(key, None)
+        # First check instance __dict__
+        if key in self.__dict__:
+            return self.__dict__[key]
+        # Then check if it's a dict method/attribute
+        if hasattr(dict, key):
+            return getattr(self, key)
+        return None
```