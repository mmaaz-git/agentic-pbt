# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `integer` validator function incorrectly accepts non-integer float values like 0.5 and 3.14, despite being named `integer` and intended to validate integer values only.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(
    value=st.floats().filter(lambda x: not x.is_integer())
)
def test_integer_validator_rejects_non_integers(value):
    """Test that integer validator rejects non-integer values."""
    try:
        integer(value)
        assert False, f"Expected ValueError for non-integer input {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(0.5)
print(f"integer(0.5) = {result}")  # Returns 0.5, should raise ValueError
print(f"int(0.5) = {int(0.5)}")    # Converts to 0, losing precision

result = integer(3.14)
print(f"integer(3.14) = {result}")  # Returns 3.14, should raise ValueError
print(f"int(3.14) = {int(3.14)}")   # Converts to 3, losing precision
```

## Why This Is A Bug

The `integer` function is meant to validate that a value can be safely converted to an integer without data loss. Currently it only checks if `int(x)` doesn't raise an exception, but `int()` silently truncates floats. This allows non-integer floats to pass validation, which violates the principle of least surprise and can lead to data corruption when decimal values are silently truncated.

## Fix

```diff
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
+        # Reject floats that aren't whole numbers
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```