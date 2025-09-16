# Bug Report: troposphere.refactorspaces boolean Function Issues

**Target**: `troposphere.refactorspaces.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` function in troposphere.refactorspaces raises ValueError with no error message and inconsistently handles case variations of boolean strings.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.refactorspaces as refactorspaces

@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_error_message(value):
    """Test that boolean() either returns a bool or raises ValueError with a message"""
    try:
        result = refactorspaces.boolean(value)
        assert isinstance(result, bool)
    except ValueError as e:
        error_msg = str(e)
        assert error_msg != "", f"ValueError raised with empty message for input: {repr(value)}"

@given(st.sampled_from([
    ("true", "True", "TRUE", "tRuE"),
    ("false", "False", "FALSE", "fAlSe")
]))
def test_boolean_case_insensitive(variations):
    """Test that boolean() handles case variations of true/false consistently"""
    results = []
    for variant in variations:
        try:
            result = refactorspaces.boolean(variant)
            results.append(result)
        except ValueError:
            results.append("ERROR")
    
    assert len(set(results)) == 1, f"Inconsistent results for case variations {variations}: {results}"
```

**Failing input**: `''` for error message test, `('true', 'True', 'TRUE', 'tRuE')` for case test

## Reproducing the Bug

```python
import troposphere.refactorspaces as refactorspaces

# Bug 1: ValueError with no error message
try:
    result = refactorspaces.boolean("")
except ValueError as e:
    print(f"Error message is empty: {str(e) == ''}")  # Prints: True

# Bug 2: Case sensitivity inconsistency
for test in ["true", "True", "TRUE", "false", "False", "FALSE"]:
    try:
        result = refactorspaces.boolean(test)
        print(f"boolean('{test}') = {result}")
    except ValueError:
        print(f"boolean('{test}') raised ValueError")
```

## Why This Is A Bug

1. **Empty error messages**: When ValueError is raised, it provides no information about what went wrong, making debugging difficult for users.

2. **Case inconsistency**: The function accepts "True" and "False" but not "TRUE" and "FALSE", which is inconsistent and unexpected for boolean string parsing.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, 1.0, "1", "true", "True"] or (isinstance(x, str) and x.lower() == "true"):
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, 0.0, "0", "false", "False"] or (isinstance(x, str) and x.lower() == "false"):
        return False
-    raise ValueError
+    raise ValueError(f"Cannot convert {repr(x)} to boolean. Expected boolean-like value.")
```