# Bug Report: troposphere.rbin.integer() OverflowError Not Caught

**Target**: `troposphere.rbin.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` function raises `OverflowError` for infinity values instead of the expected `ValueError`, causing inconsistent error handling.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.rbin as rbin

@given(st.just(float('inf')))
def test_integer_infinity_handling(x):
    """integer() should raise ValueError for all invalid inputs"""
    try:
        result = rbin.integer(x)
        assert False, f"Should have raised an error for {x}"
    except ValueError:
        pass  # Expected
    except OverflowError:
        raise AssertionError("integer() raised OverflowError instead of ValueError")
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import troposphere.rbin as rbin
from decimal import Decimal

print("Testing integer() with infinity values:")

try:
    rbin.integer(float('inf'))
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")

try:
    rbin.integer(float('-inf'))
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")

try:
    rbin.integer(Decimal('Infinity'))
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")
```

## Why This Is A Bug

The `integer()` function is designed to validate whether a value can be converted to an integer. Its implementation catches `(ValueError, TypeError)` and re-raises them as `ValueError` with a custom message. However, it doesn't catch `OverflowError` which `int()` raises for infinity values. This creates inconsistent error handling where some invalid inputs raise `ValueError` while others raise `OverflowError`, violating the expected contract that all validation failures should raise `ValueError`.

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