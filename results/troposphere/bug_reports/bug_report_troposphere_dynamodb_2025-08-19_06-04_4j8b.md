# Bug Report: troposphere.dynamodb Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.dynamodb.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` function incorrectly accepts floating-point numbers with fractional parts (e.g., 0.5, 1.5) without raising a ValueError, despite being an integer validator.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.dynamodb as ddb

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validates_correctly(x):
    """Integer function should only accept values where int(x) doesn't lose information"""
    try:
        result = ddb.integer(x)
        int_x = int(x)
        if isinstance(x, float) and x != int_x:
            assert False, f"integer() accepts non-integer float {x}"
    except (ValueError, OverflowError, TypeError):
        pass
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import troposphere.dynamodb as ddb

result = ddb.integer(0.5)
print(f"ddb.integer(0.5) = {result}")

result = ddb.integer(1.5)
print(f"ddb.integer(1.5) = {result}")

result = ddb.integer(-3.14)
print(f"ddb.integer(-3.14) = {result}")
```

## Why This Is A Bug

The `integer()` function is meant to validate integer values, but it accepts any value that can be converted to int via `int()`, including floats with fractional parts. This allows invalid non-integer values to pass validation, potentially causing issues in CloudFormation templates that expect integer values.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       if isinstance(x, float):
+           if x != int(x):
+               raise ValueError("%r is not a valid integer" % x)
+       int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```