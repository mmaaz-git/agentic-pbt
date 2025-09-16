# Bug Report: troposphere.validators Poor Error Message in Boolean Validator

**Target**: `troposphere.validators.boolean`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator raises a bare `ValueError` with no error message when given invalid inputs, making debugging difficult for users.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.one_of(st.text(), st.integers()))
def test_boolean_validator_error_messages(value):
    """Test that boolean validator provides informative error messages."""
    if value not in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"]:
        try:
            boolean(value)
        except ValueError as e:
            assert str(e) != "", f"ValueError should have a message for invalid input: {value}"
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
from troposphere.validators import boolean

result = boolean('')
```

## Why This Is A Bug

When users provide invalid boolean values, they get an uninformative `ValueError` with no message explaining what went wrong. This violates user expectations for clear error reporting and makes debugging difficult.

## Fix

```diff
def boolean(x: Any) -> bool:
    if x in [True, 1, "1", "true", "True"]:
        return True
    if x in [False, 0, "0", "false", "False"]:
        return False
-   raise ValueError
+   raise ValueError(f"Invalid boolean value: {x!r}. Expected one of: True, False, 1, 0, '1', '0', 'true', 'True', 'false', 'False'")
```