# Bug Report: requests.models.CaseInsensitiveDict Case-Folding Failure

**Target**: `requests.models.CaseInsensitiveDict`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

CaseInsensitiveDict fails to provide case-insensitive access for Unicode characters where uppercase and lowercase transformations have different lengths, such as the German 'ß' which uppercases to 'SS'.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.models

@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_case_insensitive_dict_invariant(data):
    """Test that CaseInsensitiveDict provides case-insensitive access as documented."""
    cid = requests.models.CaseInsensitiveDict(data)
    
    for key in data:
        # Test that different case variations return the same value
        assert cid.get(key) == cid.get(key.lower())
        assert cid.get(key) == cid.get(key.upper())
```

**Failing input**: `{'ß': ''}`

## Reproducing the Bug

```python
from requests.models import CaseInsensitiveDict

cid = CaseInsensitiveDict({'ß': 'value'})

print(f"cid.get('ß'): {cid.get('ß')}")      # Returns: 'value'
print(f"cid.get('SS'): {cid.get('SS')}")    # Returns: None (BUG - should be 'value')

assert cid.get('ß') == cid.get('ß'.upper())  # Fails
```

## Why This Is A Bug

The CaseInsensitiveDict documentation explicitly states:

> "querying and contains testing is case insensitive"
> "headers['content-encoding'] will return the value of a 'Content-Encoding' response header, regardless of how the header name was originally stored"

The implementation fails this contract for valid Unicode characters where case transformations change the string length. This affects:
- German 'ß' → 'SS'  
- Latin 'ŉ' → 'ʼN'
- Latin 'ǰ' → 'J̌'

While these characters are unlikely in HTTP headers, CaseInsensitiveDict is a public API that claims case-insensitive behavior without Unicode restrictions.

## Fix

The issue stems from using `.lower()` for normalization without handling case-folding edge cases. A proper fix would use Unicode case-folding:

```diff
class CaseInsensitiveDict(MutableMapping):
    def __setitem__(self, key, value):
-       self._store[key.lower()] = (key, value)
+       self._store[key.casefold()] = (key, value)
    
    def __getitem__(self, key):
-       return self._store[key.lower()][1]
+       return self._store[key.casefold()][1]
```

The `str.casefold()` method properly handles Unicode case-folding, where 'ß'.casefold() == 'ss' and 'SS'.casefold() == 'ss', ensuring consistent case-insensitive behavior.