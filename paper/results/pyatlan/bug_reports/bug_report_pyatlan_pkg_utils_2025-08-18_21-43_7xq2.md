# Bug Report: pyatlan.pkg.utils.validate_multiselect Fails on Nested Lists

**Target**: `pyatlan.pkg.utils.validate_multiselect`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `validate_multiselect` function crashes with a ValidationError when given a JSON string containing nested lists, even though such structures are valid JSON arrays.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyatlan.pkg.utils import validate_multiselect
import json

@given(st.recursive(
    st.text(min_size=1, max_size=10),
    lambda children: st.lists(children, min_size=1, max_size=3),
    max_leaves=10
))
def test_validate_multiselect_nested_structures(nested):
    json_str = json.dumps(nested)
    result = validate_multiselect(json_str)
    assert result == nested
```

**Failing input**: `[['0']]`

## Reproducing the Bug

```python
import json
from pyatlan.pkg.utils import validate_multiselect

nested_list = [["item1"]]
json_str = json.dumps(nested_list)

result = validate_multiselect(json_str)
```

## Why This Is A Bug

The function is documented to "marshal a multi-select value passed from the custom package ui". While it handles flat JSON arrays of strings correctly, it fails on nested arrays which are valid JSON structures. The function uses `parse_obj_as(List[str], data)` which strictly expects a flat list of strings, causing it to crash when the JSON contains nested structures or non-string values.

## Fix

```diff
def validate_multiselect(v):
    """
    This method is used to marshal a multi-select value passed from the custom package ui
    """
    if isinstance(v, str):
        if v.startswith("["):
            data = json.loads(v)
-            v = parse_obj_as(List[str], data)
+            # Handle nested structures or mixed types
+            if all(isinstance(item, str) for item in data):
+                v = parse_obj_as(List[str], data)
+            else:
+                # Return the parsed data as-is for complex structures
+                v = data
        else:
            v = [v]
    return v
```