# Bug Report: copier._types.LazyDict KeyError on Deletion

**Target**: `copier._types.LazyDict`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

LazyDict raises KeyError when deleting a key that hasn't been computed yet, violating standard dictionary deletion behavior.

## Property-Based Test

```python
@given(st.dictionaries(st.text(), st.integers(), min_size=1))
def test_lazydict_deletion(data):
    """Deletion should work for both pending and computed values."""
    lazy_dict = _types.LazyDict({k: lambda v=v: v for k, v in data.items()})
    
    keys_list = list(data.keys())
    # Access some values (compute them)
    for key in keys_list[:len(keys_list)//2]:
        _ = lazy_dict[key]
    
    # Delete all keys
    for key in keys_list:
        del lazy_dict[key]
        assert key not in lazy_dict
        with pytest.raises(KeyError):
            _ = lazy_dict[key]
    
    assert len(lazy_dict) == 0
```

**Failing input**: `data={'': 0}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._types import LazyDict

lazy_dict = LazyDict({'key': lambda: 'value'})
del lazy_dict['key']  # Raises KeyError: 'key'
```

## Why This Is A Bug

The `__delitem__` method unconditionally tries to delete from both `_pending` and `_done` dictionaries. If a key exists in `_pending` but hasn't been computed yet (not in `_done`), the deletion fails with KeyError. This violates the expected behavior where deleting an existing key should succeed regardless of whether its lazy value has been computed.

## Fix

```diff
--- a/copier/_types.py
+++ b/copier/_types.py
@@ -95,7 +95,7 @@ class LazyDict(MutableMapping[_K, _V]):
 
     def __delitem__(self, key: _K) -> None:
         del self._pending[key]
-        del self._done[key]
+        self._done.pop(key, None)
 
     def __iter__(self) -> Iterator[_K]:
         return iter(self._pending)
```