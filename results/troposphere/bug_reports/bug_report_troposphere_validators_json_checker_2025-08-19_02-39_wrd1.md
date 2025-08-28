# Bug Report: troposphere.validators.json_checker Rejects Valid JSON Lists

**Target**: `troposphere.validators.json_checker`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `json_checker` function incorrectly rejects Python lists, even though lists are valid JSON structures. It accepts JSON arrays as strings but not as Python lists, creating an inconsistent API.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators as validators

@given(st.one_of(
    st.just({}),
    st.just([]),
    st.just("{}"),
    st.just("[]")
))
def test_json_checker_empty_containers(data):
    """Test json_checker with empty JSON structures."""
    result = validators.json_checker(data)
    if isinstance(data, str):
        assert result == data
    else:
        assert json.loads(result) == data
```

**Failing input**: `[]`

## Reproducing the Bug

```python
import troposphere.validators as validators
import json

validators.json_checker("[]")

validators.json_checker([])
```

## Why This Is A Bug

The function accepts JSON arrays as strings ('[]', '[1,2,3]') but rejects the equivalent Python lists ([], [1,2,3]). This is inconsistent because:

1. Lists are valid JSON data structures
2. The function accepts dicts and converts them to JSON, but doesn't do the same for lists
3. The function name `json_checker` implies it should handle all JSON-serializable data
4. The asymmetry makes the API confusing - why accept dicts but not lists?

## Fix

```diff
def json_checker(prop: object) -> Any:
    from .. import AWSHelperFn

    if isinstance(prop, str):
        # Verify it is a valid json string
        json.loads(prop)
        return prop
-   elif isinstance(prop, dict):
+   elif isinstance(prop, (dict, list)):
        # Convert the dict to a basestring
        return json.dumps(prop)
    elif isinstance(prop, AWSHelperFn):
        return prop
    else:
-       raise TypeError("json object must be a str or dict")
+       raise TypeError("json object must be a str, dict, or list")
```