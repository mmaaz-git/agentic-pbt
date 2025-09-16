# Bug Report: LookupDict Dict Storage vs __dict__ Lookup Inconsistency

**Target**: `requests.structures.LookupDict`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

LookupDict inherits from dict but overrides `__getitem__` to look in `__dict__` instead of dict storage, causing severe inconsistency between dict operations and item access.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.structures import LookupDict

@given(st.text(min_size=1), st.integers())
def test_dict_storage_vs_getitem(key, value):
    ld = LookupDict(name="test")
    
    # Store using dict's __setitem__
    ld[key] = value
    
    # Should be retrievable the same way
    assert ld[key] == value  # Fails! Returns None
```

**Failing input**: Any key-value pair, e.g., `key='x', value=1`

## Reproducing the Bug

```python
from requests.structures import LookupDict

ld = LookupDict(name="test")

# Set value using dict.__setitem__
ld['key1'] = 'value1'

# Dict storage contains the value
print(dict.__getitem__(ld, 'key1'))  # 'value1'
print(len(ld))                        # 1
print(list(ld.keys()))               # ['key1']

# But __getitem__ looks in __dict__, not dict storage!
print(ld['key1'])                     # None (wrong!)
print(ld.get('key1'))                 # None (wrong!)

# Setting via attribute works differently
ld.key2 = 'value2'
print(ld['key2'])                     # 'value2' (works)
print(ld.key2)                        # 'value2' (works)
print('key2' in ld)                   # False (wrong!)
```

## Why This Is A Bug

LookupDict inherits from dict but breaks the fundamental dict contract:
1. Values stored with `ld[key] = value` cannot be retrieved with `ld[key]`
2. The `get()` method doesn't access dict storage
3. Dict methods (keys(), values(), items(), len()) operate on dict storage but `__getitem__` doesn't
4. This violates the Liskov Substitution Principle - LookupDict cannot be used as a dict

The class creates two separate storage mechanisms that don't interact properly, leading to confusing and incorrect behavior.

## Fix

The class needs a complete redesign. Either:
1. Don't inherit from dict and implement a custom mapping that only uses `__dict__`
2. Remove the `__getitem__` override to use normal dict behavior
3. Make `__getitem__` check both storages:

```diff
--- a/requests/structures.py
+++ b/requests/structures.py
@@ -96,8 +96,11 @@ class LookupDict(dict):
 
     def __getitem__(self, key):
         # We allow fall-through here, so values default to None
-
-        return self.__dict__.get(key, None)
+        # Check dict storage first, then __dict__
+        try:
+            return dict.__getitem__(self, key)
+        except KeyError:
+            return self.__dict__.get(key, None)
 
     def get(self, key, default=None):
-        return self.__dict__.get(key, default)
+        try:
+            return self[key]
+        except KeyError:
+            return default
```