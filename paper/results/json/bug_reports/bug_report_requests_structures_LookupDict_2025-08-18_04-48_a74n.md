# Bug Report: requests.structures.LookupDict Breaks Dict Contract

**Target**: `requests.structures.LookupDict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

LookupDict's `__getitem__` and `get()` methods incorrectly use `self.__dict__` instead of the parent dict's storage, causing all dict-stored values to be inaccessible and always return None.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.structures import LookupDict

@given(st.text(min_size=1), st.integers())
def test_lookupdict_getitem_vs_dict_storage(key, value):
    ld = LookupDict(name="test")
    dict.__setitem__(ld, key, value)
    
    assert key in ld  # True - dict's __contains__ works
    result = ld[key]  # But this returns None!
    assert result is None  # BUG: Should return value
```

**Failing input**: Any key-value pair, e.g., `('a', 1)`

## Reproducing the Bug

```python
from requests.structures import LookupDict

ld = LookupDict(name="test")
ld["key"] = "value"

print(f"'key' in ld: {'key' in ld}")  # True
print(f"len(ld): {len(ld)}")  # 1
print(f"ld['key']: {ld['key']}")  # None (BUG: should be "value")
print(f"ld.get('key'): {ld.get('key')}")  # None (BUG: should be "value")

import requests
requests.codes["custom"] = 999
print(f"'custom' in codes: {'custom' in requests.codes}")  # True
print(f"codes['custom']: {requests.codes['custom']}")  # None (BUG: should be 999)
```

## Why This Is A Bug

This violates the fundamental dict contract: if `key in dict` returns True, then `dict[key]` must return the associated value, not None. The current implementation makes LookupDict unusable as a normal dict, breaking polymorphism and the Liskov Substitution Principle. Any code expecting dict-like behavior will fail when given a LookupDict instance.

## Fix

```diff
--- a/requests/structures.py
+++ b/requests/structures.py
@@ -90,11 +90,13 @@ class LookupDict(dict):
         return f"<lookup '{self.name}'>"
 
     def __getitem__(self, key):
-        # We allow fall-through here, so values default to None
-        
-        return self.__dict__.get(key, None)
+        # First check __dict__ for attribute-style access
+        if key in self.__dict__:
+            return self.__dict__[key]
+        # Fall back to parent dict storage
+        return dict.__getitem__(self, key)
 
     def get(self, key, default=None):
-        return self.__dict__.get(key, default)
+        try:
+            return self[key]
+        except KeyError:
+            return default
```