# Bug Report: troposphere.pipes.integer OverflowError with Infinity

**Target**: `troposphere.pipes.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` function raises `OverflowError` instead of `ValueError` when given infinity values, violating its documented error contract.

## Property-Based Test

```python
import troposphere.pipes
from hypothesis import given, strategies as st
import pytest


@given(st.one_of(st.just(float('inf')), st.just(float('-inf'))))
def test_integer_infinity_should_raise_valueerror(x):
    """
    The integer function should raise ValueError for infinity values,
    not OverflowError, and include the specific message format.
    """
    with pytest.raises(ValueError) as excinfo:
        troposphere.pipes.integer(x)
    assert "%r is not a valid integer" % x in str(excinfo.value)
```

**Failing input**: `inf`

## Reproducing the Bug

```python
import troposphere.pipes

try:
    troposphere.pipes.integer(float('inf'))
except OverflowError as e:
    print(f"Bug confirmed: OverflowError raised instead of ValueError")
    print(f"Error message: {e}")

try:
    troposphere.pipes.integer(float('-inf'))
except OverflowError as e:
    print(f"Bug confirmed: OverflowError raised for -inf too")
    print(f"Error message: {e}")
```

## Why This Is A Bug

The function's implementation catches `ValueError` and `TypeError` to provide a consistent error message format: `"%r is not a valid integer"`. However, it doesn't catch `OverflowError` which occurs when converting infinity to int. This violates the API contract that invalid inputs should raise `ValueError` with a specific message format.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
-   except (ValueError, TypeError):
+   except (ValueError, TypeError, OverflowError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```