# Bug Report: requests.status_codes LookupDict Attribute Access Inconsistency

**Target**: `requests.status_codes.LookupDict`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

LookupDict's `__getitem__` method returns None for inherited dict methods instead of the actual methods, causing inconsistency with attribute access.

## Property-Based Test

```python
def test_lookupdict_attribute_consistency():
    """
    Property: For a dict-like object, obj[key] should be consistent with 
    getattr(obj, key) when key is a string representing an attribute name.
    """
    codes = requests.status_codes.codes
    
    for attr in dir(codes):
        if not attr.startswith('_'):
            dict_access = codes[attr]
            attr_access = getattr(codes, attr)
            assert dict_access == attr_access
```

**Failing input**: `'clear'` (and other inherited dict methods like 'copy', 'items', 'keys', etc.)

## Reproducing the Bug

```python
import requests.status_codes

codes = requests.status_codes.codes

print(f"codes['clear'] = {codes['clear']}")
print(f"codes.clear = {codes.clear}")

assert codes['clear'] == getattr(codes, 'clear'), "Inconsistent access!"
```

## Why This Is A Bug

This violates the expected behavior for dict-like objects where `obj[key]` should be consistent with `getattr(obj, key)` for string keys. The current implementation only checks `self.__dict__` which doesn't include inherited methods, causing:
- `codes.clear` returns the clear method
- `codes['clear']` returns None
- This breaks dynamic attribute access patterns where code expects `obj[key]` to work like attribute access

## Fix

```diff
--- a/requests/status_codes.py
+++ b/requests/status_codes.py
@@ -10,8 +10,11 @@ class LookupDict(dict):
         return f"<lookup '{self.name}'>"
 
     def __getitem__(self, key):
-        # We allow fall-through here, so values default to None
-        return self.__dict__.get(key, None)
+        # First check instance __dict__, then fall back to getattr for inherited attributes
+        if key in self.__dict__:
+            return self.__dict__[key]
+        # For inherited attributes, return them if they exist, otherwise None
+        return getattr(self, key, None) if hasattr(self, key) else None
 
     def get(self, key, default=None):
-        return self.__dict__.get(key, default)
+        return self[key] if self[key] is not None else default
```