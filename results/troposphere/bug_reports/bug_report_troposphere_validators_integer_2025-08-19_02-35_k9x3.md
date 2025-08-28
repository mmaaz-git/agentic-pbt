# Bug Report: troposphere.validators.integer crashes on infinity values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer` validator function crashes with an unhandled `OverflowError` when given float infinity values, instead of properly raising a `ValueError` as expected.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text()
))
def test_integer_validator_property(value):
    try:
        result = integer(value)
        int_val = int(value)
        assert result == value
    except (ValueError, TypeError):
        try:
            int(value)
            assert False, f"integer() rejected {value} but int() accepted it"
        except (ValueError, TypeError):
            pass
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(float('inf'))
```

## Why This Is A Bug

The `integer` validator is designed to validate integer values and raise `ValueError` for invalid inputs. However, it doesn't catch `OverflowError` that occurs when `int()` is called on infinity values. This violates the expected contract where invalid inputs should result in a `ValueError`, not an unhandled exception.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```