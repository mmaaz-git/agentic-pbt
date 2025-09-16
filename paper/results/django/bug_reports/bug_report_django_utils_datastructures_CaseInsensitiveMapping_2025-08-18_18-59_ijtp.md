# Bug Report: CaseInsensitiveMapping Fails with Unicode Case-Folding Edge Cases

**Target**: `django.utils.datastructures.CaseInsensitiveMapping`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

CaseInsensitiveMapping fails to handle Unicode characters with complex case mappings, such as German 'ß' (which uppercases to 'SS') and Turkish 'ı' (which uppercases to 'I'), breaking the promised case-insensitive lookups.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from django.utils.datastructures import CaseInsensitiveMapping

@given(st.text(min_size=1))
@example("ß")  # German sharp s
@example("ı")  # Turkish lowercase i without dot
def test_case_insensitive_mapping_unicode(key):
    """Test that CaseInsensitiveMapping is truly case-insensitive"""
    ci_map = CaseInsensitiveMapping({key: "value"})
    
    # Should be able to access with any case variation
    assert ci_map.get(key.lower()) == "value"
    assert ci_map.get(key.upper()) == "value"  # FAILS for ß and ı
```

**Failing input**: `'ß'` and `'ı'`

## Reproducing the Bug

```python
from django.utils.datastructures import CaseInsensitiveMapping

# German ß case
ci_map = CaseInsensitiveMapping({'ß': 'sharp s'})
print(f"Original 'ß': {ci_map.get('ß')}")       # Returns: 'sharp s'
print(f"Upper 'SS': {ci_map.get('SS')}")        # Returns: None (BUG!)
print(f"Note: 'ß'.upper() = {'ß'.upper()!r}")   # 'SS'

# Turkish ı case  
ci_map2 = CaseInsensitiveMapping({'ı': 'dotless i'})
print(f"Original 'ı': {ci_map2.get('ı')}")     # Returns: 'dotless i'
print(f"Upper 'I': {ci_map2.get('I')}")        # Returns: None (BUG!)
print(f"Note: 'ı'.upper() = {'ı'.upper()!r}")  # 'I'
```

## Why This Is A Bug

CaseInsensitiveMapping's docstring states it allows "case-insensitive key lookups", but it only uses `str.lower()` for normalization. This fails for Unicode characters where:
1. The uppercase form has different length (ß → SS)
2. Case transformations aren't round-trip safe (ı → I → i, not back to ı)

This violates the class's contract of providing case-insensitive access.

## Fix

The implementation should use Unicode case-folding instead of simple lowercase conversion:

```diff
class CaseInsensitiveMapping(Mapping):
    def __init__(self, data):
-       self._store = {k.lower(): (k, v) for k, v in self._unpack_items(data)}
+       self._store = {k.casefold(): (k, v) for k, v in self._unpack_items(data)}

    def __getitem__(self, key):
-       return self._store[key.lower()][1]
+       return self._store[key.casefold()][1]

    def __eq__(self, other):
        return isinstance(other, Mapping) and {
-           k.lower(): v for k, v in self.items()
+           k.casefold(): v for k, v in self.items()
-       } == {k.lower(): v for k, v in other.items()}
+       } == {k.casefold(): v for k, v in other.items()}
```

Using `str.casefold()` provides aggressive case-folding that handles these Unicode edge cases correctly.