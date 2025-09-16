# Bug Report: CaseInsensitiveDict Unicode Case Conversion Failure

**Target**: `requests.structures.CaseInsensitiveDict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

CaseInsensitiveDict fails to handle Unicode characters whose uppercase and lowercase conversions are not reversible, violating its case-insensitive lookup guarantee.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.structures import CaseInsensitiveDict

@given(st.text(min_size=1), st.integers())
def test_case_insensitive_retrieval(key, value):
    cid = CaseInsensitiveDict()
    cid[key] = value
    
    # Should be retrievable with any case variation
    assert cid[key.lower()] == value
    assert cid[key.upper()] == value
```

**Failing input**: `key='ß'` (German sharp S)

## Reproducing the Bug

```python
from requests.structures import CaseInsensitiveDict

cid = CaseInsensitiveDict()
cid['ß'] = 'sharp_s_value'

# This raises KeyError: 'ss'
# Because 'ß'.upper() == 'SS' but 'SS'.lower() == 'ss' (not 'ß')
value = cid['SS']
```

## Why This Is A Bug

The CaseInsensitiveDict documentation states that "querying and contains testing is case insensitive" and provides the example `cid['aCCEPT'] == 'application/json'`. However, for certain Unicode characters like:
- German sharp S (ß → SS → ss)
- Turkish dotless i (ı → I → i)  
- Micro sign (µ → Μ → μ)

The case conversion is not reversible, causing lookups to fail. This violates the documented behavior that lookups should work regardless of case.

## Fix

The issue is that the implementation assumes `key.upper().lower() == key.lower()`, which doesn't hold for all Unicode. A proper fix would use Unicode case folding:

```diff
--- a/requests/structures.py
+++ b/requests/structures.py
@@ -45,11 +45,11 @@ class CaseInsensitiveDict(MutableMapping):
     def __setitem__(self, key, value):
         # Use the lowercased key for lookups, but store the actual
         # key alongside the value.
-        self._store[key.lower()] = (key, value)
+        self._store[key.casefold()] = (key, value)
 
     def __getitem__(self, key):
-        return self._store[key.lower()][1]
+        return self._store[key.casefold()][1]
 
     def __delitem__(self, key):
-        del self._store[key.lower()]
+        del self._store[key.casefold()]
```

The `str.casefold()` method is designed specifically for caseless matching and handles these Unicode edge cases correctly.