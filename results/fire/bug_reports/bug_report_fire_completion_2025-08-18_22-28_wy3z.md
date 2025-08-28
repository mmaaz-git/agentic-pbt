# Bug Report: fire.completion Dictionary Key Transformation

**Target**: `fire.completion.Completions`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `Completions` function incorrectly transforms dictionary keys containing underscores to use hyphens, preventing proper tab completion for dictionary access.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.completion as completion

@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: not x.startswith('_')),
    st.one_of(st.integers(), st.text(), st.none())
))
def test_completions_dict_keys_not_values(d):
    """Completions for dicts should be the keys, not the values."""
    if not d:
        return
    completions = completion.Completions(d)
    for key in d.keys():
        assert key in completions
```

**Failing input**: `{'0_': None}`

## Reproducing the Bug

```python
import fire.completion as completion

test_dict = {'foo_bar': None, 'baz_qux': 42, 'hello_world': 'test'}

completions = completion.Completions(test_dict)
print("Dictionary keys:", list(test_dict.keys()))
print("Completions:", completions)

for key in test_dict.keys():
    assert key in completions, f"Key '{key}' not found, but '{key.replace('_', '-')}' is present"
```

## Why This Is A Bug

Dictionary keys are literal identifiers that should be preserved exactly as defined. When Fire transforms `foo_bar` to `foo-bar` in completions, users cannot use tab completion to access `dict['foo_bar']` because the suggested completion `foo-bar` doesn't match the actual key. This violates the expected behavior where completions should help users access the exact members of a data structure.

## Fix

```diff
--- a/fire/completion.py
+++ b/fire/completion.py
@@ -410,9 +410,16 @@ def Completions(component, verbose=False):
     # TODO(dbieber): There are currently no commands available for generators.
     return []
 
+  # For dictionaries, return keys without transformation
+  if isinstance(component, dict):
+    return [
+        member_name
+        for member_name, _ in VisibleMembers(component, verbose=verbose)
+    ]
+
+  # For other components, apply command formatting
   return [
       _FormatForCommand(member_name)
       for member_name, _ in VisibleMembers(component, verbose=verbose)
   ]
```