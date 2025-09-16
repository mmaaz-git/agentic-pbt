# Bug Report: troposphere.validators.integer OverflowError on Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `integer` validator function crashes with an unhandled `OverflowError` when given float infinity values, instead of raising the expected `ValueError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.floats())
def test_integer_validator_handles_all_floats(x):
    """
    The integer validator should either:
    1. Successfully validate the input and return it, OR
    2. Raise a ValueError with a descriptive message
    
    It should NEVER raise other exceptions like OverflowError.
    """
    try:
        result = integer(x)
        int_value = int(x)
    except ValueError as e:
        assert "%r is not a valid integer" % x in str(e)
    except OverflowError:
        pytest.fail(f"integer({x}) raised OverflowError instead of ValueError")
```

**Failing input**: `inf` (positive infinity)

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(float('inf'))
```

## Why This Is A Bug

The `integer` validator is designed to validate inputs and raise `ValueError` with a descriptive message when validation fails. The function catches `ValueError` and `TypeError` but not `OverflowError`, which occurs when converting infinity to an integer. This inconsistency means:

1. Users cannot reliably catch validation errors with a single exception type
2. The error message is less informative (generic Python error vs. custom validation message)
3. The validator doesn't fulfill its contract of providing consistent error handling

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```