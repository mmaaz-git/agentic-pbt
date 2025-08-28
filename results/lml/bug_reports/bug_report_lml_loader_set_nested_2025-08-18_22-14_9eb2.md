# Bug Report: lml_loader Set Nested Value Crashes on Non-Dict Path

**Target**: `lml_loader.DataLoader.set_nested_value`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `set_nested_value` method crashes with a TypeError when attempting to set a nested value through a path that contains non-dict values, failing to handle the case where intermediate values are not dictionaries.

## Property-Based Test

```python
@given(
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.integers()
)
def test_set_nested_value_overwrites_non_dict(key1, key2, value):
    loader = DataLoader()
    data = {key1: "not a dict"}
    path = f"{key1}.{key2}"
    updated = loader.set_nested_value(data, path, value)
    assert isinstance(updated[key1], dict)
    assert updated[key1][key2] == value
```

**Failing input**: `data={'A': 'string'}`, `path='A.B'`, `value=0`

## Reproducing the Bug

```python
from lml_loader import DataLoader

loader = DataLoader()

# Case 1: String value in path
data = {'config': 'simple_string'}
try:
    result = loader.set_nested_value(data, 'config.timeout', 30)
except TypeError as e:
    print(f"Error: {e}")

# Case 2: Integer value in path  
data = {'version': 1}
try:
    result = loader.set_nested_value(data, 'version.major', 2)
except TypeError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

The function should either gracefully handle non-dict values in the path by replacing them with dictionaries, or raise a more informative error. Currently it crashes with a cryptic "object does not support item assignment" error that doesn't help users understand what went wrong.

## Fix

```diff
--- a/lml_loader.py
+++ b/lml_loader.py
@@ -91,8 +91,11 @@ class DataLoader:
         
         for key in keys[:-1]:
             if key not in current:
                 current[key] = {}
-            current = current[key]
+            elif not isinstance(current[key], dict):
+                current[key] = {}
+            current = current[key]
         
         current[keys[-1]] = value
         return result
```