# Bug Report: CaseInsensitiveDict Unicode Case-Folding Bug

**Target**: `requests.structures.CaseInsensitiveDict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

CaseInsensitiveDict fails to handle Unicode case-folding correctly, causing lookups to fail for characters with complex case mappings like German ß (sharp s) which uppercases to 'SS'.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from requests.structures import CaseInsensitiveDict

@given(st.text(min_size=1, max_size=20))
@example("ß")  # German sharp s
def test_case_insensitive_dict_unicode(key):
    """Test CaseInsensitiveDict with Unicode case variations."""
    cid = CaseInsensitiveDict()
    cid[key] = "value1"
    
    # Should handle case-insensitive lookup
    assert cid.get(key.lower()) == "value1"
    assert cid.get(key.upper()) == "value1"  # FAILS for ß
```

**Failing input**: `'ß'`

## Reproducing the Bug

```python
from requests.structures import CaseInsensitiveDict

cid = CaseInsensitiveDict()
cid['ß'] = 'value'

print(cid.get('ß'))   # 'value' ✓
print(cid.get('SS'))  # None ✗ (should be 'value')
print(cid.get('ss'))  # None ✗ (should be 'value')

print('ß'.upper())    # 'SS'
print('ß'.lower())    # 'ß'
print('SS'.lower())   # 'ss'
```

## Why This Is A Bug

CaseInsensitiveDict claims to provide case-insensitive lookups for string keys. However, it uses Python's `.lower()` method for normalization, which doesn't handle Unicode case-folding correctly. The German character 'ß' uppercases to 'SS', but since 'ß'.lower() != 'ss', lookups fail for the uppercase variant.

This violates the expected behavior that if `key1.upper() == key2.upper()` or `key1.lower() == key2.lower()`, then `dict[key1]` and `dict[key2]` should return the same value in a case-insensitive dictionary.

## Fix

```diff
--- a/requests/structures.py
+++ b/requests/structures.py
@@ -40,15 +40,16 @@ class CaseInsensitiveDict(MutableMapping):
         self._store = OrderedDict()
         if data is None:
             data = {}
         self.update(data, **kwargs)
 
     def __setitem__(self, key, value):
         # Use the lowercased key for lookups, but store the actual
         # key alongside the value.
-        self._store[key.lower()] = (key, value)
+        # Use casefold() for proper Unicode case-insensitive comparison
+        self._store[key.casefold()] = (key, value)
 
     def __getitem__(self, key):
-        return self._store[key.lower()][1]
+        return self._store[key.casefold()][1]
 
     def __delitem__(self, key):
-        del self._store[key.lower()]
+        del self._store[key.casefold()]
```

Note: Python's `str.casefold()` provides proper Unicode case-folding and would fix this issue. It's available in Python 3.3+, which should be compatible with modern versions of requests.