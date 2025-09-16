# Bug Report: troposphere.validators.boolean Case Sensitivity Inconsistency

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator function inconsistently handles case variations of "true" and "false" strings, accepting lowercase and Title case but rejecting UPPERCASE variants.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.sampled_from(["true", "false"]))
def test_boolean_validator_case_insensitive(base_value):
    variations = [
        base_value.lower(),
        base_value.upper(), 
        base_value.capitalize()
    ]
    
    results = []
    for variant in variations:
        try:
            results.append(boolean(variant))
        except ValueError:
            results.append(None)
    
    # All variations should produce same result
    assert all(r == results[0] for r in results), \
        f"Inconsistent results for {base_value}: {results}"
```

**Failing input**: `"true"` produces `[True, None, True]` for `["true", "TRUE", "True"]`

## Reproducing the Bug

```python
from troposphere.validators import boolean

print(boolean("true"))   # Returns True
print(boolean("True"))   # Returns True  
print(boolean("TRUE"))   # Raises ValueError

print(boolean("false"))  # Returns False
print(boolean("False"))  # Returns False
print(boolean("FALSE"))  # Raises ValueError
```

## Why This Is A Bug

The validator accepts both lowercase ("true") and Title case ("True") but rejects uppercase ("TRUE"), creating an inconsistent API. Users reasonably expect all case variations to be handled uniformly, especially since the function already handles some case variations.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, "1", "true", "True", "TRUE"]:
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, "0", "false", "False", "FALSE"]:
        return False
    raise ValueError
```