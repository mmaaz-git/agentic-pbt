# Bug Report: requests.sessions.merge_setting Inconsistent None Value Removal

**Target**: `requests.sessions.merge_setting`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `merge_setting` function inconsistently handles None values in dictionaries - it removes them when merging two dictionaries but preserves them when returning a single dictionary.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.sessions import merge_setting

@given(
    base_dict=st.one_of(st.none(), st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.none()))),
    override_dict=st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.none()))
)
def test_merge_setting_none_removal_consistency(base_dict, override_dict):
    """Test that merge_setting consistently removes None values from dicts"""
    result = merge_setting(override_dict, base_dict)
    
    if result is not None and isinstance(result, dict):
        # None values should always be removed from dictionary results
        assert None not in result.values()
```

**Failing input**: `base_dict=None, override_dict={'0': None}`

## Reproducing the Bug

```python
from requests.sessions import merge_setting

# Case 1: Both arguments are dicts - None values ARE removed
result1 = merge_setting({'a': 1, 'b': None}, {'c': 2})
print(f"Both dicts: {result1}")
print(f"Has None values: {None in result1.values()}")

# Case 2: Session setting is None - None values are NOT removed
result2 = merge_setting({'a': 1, 'b': None}, None)
print(f"\nSession None: {result2}")
print(f"Has None values: {None in result2.values()}")

# Case 3: Request setting is None - None values are NOT removed
result3 = merge_setting(None, {'a': 1, 'b': None})
print(f"\nRequest None: {result3}")
print(f"Has None values: {None in result3.values()}")
```

## Why This Is A Bug

The function contains code to "Remove keys that are set to None" with an explicit comment stating this intent. However, this removal only occurs when both arguments are Mapping objects. When one argument is None, the dictionary is returned as-is with None values intact, violating the documented behavior and creating inconsistent results based on whether settings are being merged or not.

## Fix

```diff
def merge_setting(request_setting, session_setting, dict_class=OrderedDict):
    """Determines appropriate setting for a given request, taking into account
    the explicit setting on that request, and the setting in the session. If a
    setting is a dictionary, they will be merged together using `dict_class`
    """

    if session_setting is None:
-       return request_setting
+       if isinstance(request_setting, Mapping):
+           # Remove None values from the dictionary before returning
+           result = dict_class(to_key_val_list(request_setting))
+           none_keys = [k for (k, v) in result.items() if v is None]
+           for key in none_keys:
+               del result[key]
+           return result
+       return request_setting

    if request_setting is None:
-       return session_setting
+       if isinstance(session_setting, Mapping):
+           # Remove None values from the dictionary before returning
+           result = dict_class(to_key_val_list(session_setting))
+           none_keys = [k for (k, v) in result.items() if v is None]
+           for key in none_keys:
+               del result[key]
+           return result
+       return session_setting

    # Bypass if not a dictionary (e.g. verify)
    if not (
        isinstance(session_setting, Mapping) and isinstance(request_setting, Mapping)
    ):
        return request_setting

    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))

    # Remove keys that are set to None. Extract keys first to avoid altering
    # the dictionary during iteration.
    none_keys = [k for (k, v) in merged_setting.items() if v is None]
    for key in none_keys:
        del merged_setting[key]

    return merged_setting
```