# Bug Report: CaseInsensitiveDict Fails with Unicode Characters Having Complex Case Mappings

**Target**: `azure.core.utils.CaseInsensitiveDict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

CaseInsensitiveDict fails to provide case-insensitive access for Unicode characters with complex case mappings, such as 'µ' (micro sign) and 'ß' (German sharp s).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from azure.core.utils import CaseInsensitiveDict

@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != ''),
        st.text(max_size=100),
        min_size=1,
        max_size=20
    )
)
def test_case_insensitive_dict_access_invariant(test_dict):
    ci_dict = CaseInsensitiveDict(test_dict)
    
    for key, value in test_dict.items():
        assert ci_dict.get(key.lower()) == value
        assert ci_dict.get(key.upper()) == value
        assert ci_dict.get(key.title()) == value
```

**Failing input**: `{'µ': ''}` (micro sign character)

## Reproducing the Bug

```python
from azure.core.utils import CaseInsensitiveDict

# Bug 1: Micro sign case mapping issue
ci_dict = CaseInsensitiveDict({'µ': 'micro'})
print(f"'µ'.upper() = {repr('µ'.upper())}")  # Returns 'Μ' (Greek capital Mu)
print(f"ci_dict['µ'] = {ci_dict.get('µ')}")  # Returns 'micro'
print(f"ci_dict['Μ'] = {ci_dict.get('Μ')}")  # Returns None (should return 'micro')

# Bug 2: German sharp s creates duplicate keys
ci_dict2 = CaseInsensitiveDict()
ci_dict2['ß'] = 'lower'
ci_dict2['SS'] = 'upper'
print(f"'ß'.upper() = {repr('ß'.upper())}")  # Returns 'SS'
print(f"Dict keys: {list(ci_dict2.keys())}")  # Shows ['ß', 'SS']
print(f"Dict length: {len(ci_dict2)}")  # Returns 2 (should be 1)
```

## Why This Is A Bug

CaseInsensitiveDict is documented as providing case-insensitive access to keys. However, it uses Python's `.lower()` method for key normalization, which doesn't properly handle Unicode characters with complex case mappings:

1. **Micro sign (µ)**: Uppercases to Greek capital Mu (Μ), but Μ.lower() = 'μ' (Greek lowercase mu), not 'µ'
2. **German sharp s (ß)**: Uppercases to 'SS', but 'SS'.lower() = 'ss', not 'ß'

This violates the fundamental invariant that accessing a key with any case variation should return the same value.

## Fix

The fix requires using proper Unicode case folding instead of simple `.lower()`:

```diff
--- a/azure/core/utils/_utils.py
+++ b/azure/core/utils/_utils.py
@@ -123,7 +123,7 @@ class CaseInsensitiveDict(MutableMapping[str, Any]):
         self._data: Dict[str, Any] = {}
         if data is None:
             data = {}
         self.update(data, **kwargs)
 
     def __setitem__(self, key: str, value: Any) -> None:
-        self._data[key.lower()] = (key, value)
+        self._data[key.casefold()] = (key, value)
 
     def __getitem__(self, key: str) -> Any:
-        return self._data[key.lower()][1]
+        return self._data[key.casefold()][1]
 
     def __delitem__(self, key: str) -> None:
-        del self._data[key.lower()]
+        del self._data[key.casefold()]
 
     # Similar changes needed for get(), pop(), setdefault(), etc.
```

Note: `str.casefold()` is the Unicode-aware case folding method designed specifically for caseless matching.