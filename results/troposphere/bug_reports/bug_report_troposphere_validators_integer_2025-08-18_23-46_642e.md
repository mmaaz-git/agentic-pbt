# Bug Report: troposphere.validators.integer Accepts Non-Integer Types

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `integer()` validator function incorrectly accepts boolean and float values without raising exceptions, returning them unchanged instead of validating that inputs are actual integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(value=st.one_of(
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_integer_validator_should_reject_non_integers(value):
    """The integer validator should reject booleans and floats"""
    result = integer(value)
    # Bug: Returns the original non-integer value instead of raising
    assert result == value
    assert type(result) in (bool, float)
```

**Failing input**: `False`, `True`, `0.0`, `3.14`, etc.

## Reproducing the Bug

```python
from troposphere.validators import integer

# These should raise ValueError but don't
print(integer(False))   # Returns: False (bool)
print(integer(True))    # Returns: True (bool)  
print(integer(0.0))     # Returns: 0.0 (float)
print(integer(3.14))    # Returns: 3.14 (float)
```

## Why This Is A Bug

The `integer()` validator's purpose is to ensure values are integers for CloudFormation template properties. Accepting booleans and floats violates type safety expectations:

1. Booleans are semantically different from integers in CloudFormation contexts
2. Floats with fractional parts (e.g., 3.14) pass validation unchanged, which could cause downstream issues
3. The function name `integer()` implies strict integer validation

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    # Reject booleans explicitly (they pass int() but aren't integers)
+    if isinstance(x, bool):
+        raise ValueError("%r is not a valid integer" % x)
+    # Reject floats that aren't integer values
+    if isinstance(x, float):
+        if not x.is_integer():
+            raise ValueError("%r is not a valid integer" % x)
+        # Convert integer-valued floats to int
+        x = int(x)
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```