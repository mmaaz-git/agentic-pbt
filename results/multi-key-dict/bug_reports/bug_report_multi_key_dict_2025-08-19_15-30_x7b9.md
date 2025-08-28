# Bug Report: multi_key_dict get_other_keys() Returns Self When Duplicate Keys Exist

**Target**: `multi_key_dict.get_other_keys()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_other_keys()` method incorrectly includes the queried key in its result when the multi-key mapping contains duplicate keys, violating the method's documented contract of returning only "other" keys.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import multi_key_dict

@given(
    key=st.integers(),
    other_key=st.integers(),
    duplicate_count=st.integers(min_value=2, max_value=5)
)
def test_get_other_keys_with_duplicates(key, other_key, duplicate_count):
    """get_other_keys should never return the queried key itself"""
    # Create keys list with duplicates
    keys = [key] * duplicate_count + [other_key]
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = 'value'
    
    # get_other_keys should not include the queried key
    others = m.get_other_keys(key)
    assert key not in others, f"Key {key} found in its own get_other_keys(): {others}"
```

**Failing input**: `key=1, other_key=2, duplicate_count=2` (produces keys `[1, 1, 2]`)

## Reproducing the Bug

```python
import multi_key_dict

m = multi_key_dict.multi_key_dict()
m['a', 'a', 'b'] = 'value'
result = m.get_other_keys('a')
print(f"get_other_keys('a') = {result}")
assert 'a' not in result, f"Bug: 'a' found in get_other_keys('a'): {result}"
```

## Why This Is A Bug

The method's docstring states it returns "list of other keys that are mapped to the same value" with the parameter `including_current` controlling whether to include the queried key. When `including_current=False` (default), the queried key should never appear in the result. However, when duplicate keys exist in the mapping, the method incorrectly returns the queried key due to improper handling of duplicates in the removal logic.

## Fix

The bug is in the `get_other_keys` method at lines 173-175. The current implementation removes only one occurrence of the key, but when duplicates exist, additional occurrences remain.

```diff
def get_other_keys(self, key, including_current=False):
    """ Returns list of other keys that are mapped to the same value as specified key. 
        @param key - key for which other keys should be returned.
        @param including_current if set to True - key will also appear on this list."""
    other_keys = []
    if key in self:
        other_keys.extend(self.__dict__[str(type(key))][key])
        if not including_current:
-            other_keys.remove(key)
+            # Remove all occurrences of the key, not just one
+            other_keys = [k for k in other_keys if k != key]
    return other_keys
```