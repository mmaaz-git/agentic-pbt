# Bug Report: troposphere.validators.double Raises OverflowError Instead of ValueError

**Target**: `troposphere.validators.double`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double` validator function raises an uncaught `OverflowError` for very large integers that cannot be converted to float, violating its contract to only raise `ValueError` for invalid inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.quicksight as qs

@given(st.integers(min_value=10**300, max_value=10**310))
def test_double_large_integers(value):
    """Test double with very large integers."""
    result = qs.double(value)
    assert result == value
```

**Failing input**: `180997900164495250545713473750996638066097323906379518688947625868304008083125893053680361863241261960966842431062909935002961630547993526749280464108505091606551958166521933571330983251375522703463170753641505299138865107116052174892565569623577812486773889483228888172017249369353616859339437710999160848260`

## Reproducing the Bug

```python
import troposphere.validators as validators

large_int = 10**310
try:
    result = validators.double(large_int)
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (unexpected!): {e}")
```

## Why This Is A Bug

The `double` function is designed to validate inputs that can be converted to floating-point numbers. According to its implementation, it should either:
1. Return the input unchanged if `float(x)` succeeds
2. Raise `ValueError` with message "%r is not a valid double" if conversion fails

However, the function only catches `ValueError` and `TypeError` from `float()`, missing `OverflowError` which occurs for integers too large to represent as floats. This breaks the function's contract and can cause unexpected exceptions in calling code that only expects `ValueError`.

## Fix

```diff
def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
    try:
        float(x)
-   except (ValueError, TypeError):
+   except (ValueError, TypeError, OverflowError):
        raise ValueError("%r is not a valid double" % x)
    else:
        return x
```