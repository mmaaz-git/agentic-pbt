# Bug Report: troposphere.validators integer() Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator incorrectly accepts float values like 0.5 and 3.14, violating its contract to validate integer values only.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.floats())
def test_integer_validator_rejects_non_integer_floats(value):
    """Test that integer validator rejects non-integer float values"""
    if isinstance(value, float) and not value.is_integer():
        try:
            integer(value)
            assert False, f"integer() should have rejected {value}"
        except (ValueError, TypeError):
            pass
```

**Failing input**: `value=0.5`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(0.5)
print(f"integer(0.5) returned: {result}")
print(f"Type: {type(result)}")

result = integer(3.14)
print(f"integer(3.14) returned: {result}")
print(f"Type: {type(result)}")
```

## Why This Is A Bug

The `integer()` validator is supposed to validate that a value is an integer. However, it accepts float values like 0.5 and 3.14, returning them unchanged. This violates the principle of least surprise - a validator named "integer" should reject non-integer values.

The bug occurs because the validator only checks if `int(x)` succeeds (which truncates floats) but then returns the original value instead of either:
1. Rejecting non-integer floats
2. Returning the converted integer value

## Fix

The validator should either reject non-integer floats or return the converted value:

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       int_value = int(x)
+       # Reject if conversion changes the value (i.e., x was a non-integer float)
+       if isinstance(x, float) and int_value != x:
+           raise ValueError("%r is not a valid integer" % x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```