# Bug Report: troposphere.validators.integer OverflowError on Infinity Values

**Target**: `troposphere.validators.integer`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer()` validator function raises `OverflowError` instead of the expected `ValueError` when given float infinity values, breaking exception handling consistency.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(value=st.one_of(
    st.integers(),
    st.text(alphabet=string.digits, min_size=1, max_size=10),
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.floats()
))
def test_integer_validator(value):
    try:
        result = integer(value)
        int(result)
        int(value)
    except (ValueError, TypeError):
        try:
            integer(value)
            int(value)
            assert False, f"integer() accepted {value!r} but shouldn't have"
        except ValueError:
            pass
```

**Failing input**: `inf`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(float('inf'))
```

## Why This Is A Bug

The `integer()` validator is expected to raise `ValueError` for invalid inputs that cannot be converted to integers, as documented by the error message pattern "%r is not a valid integer". However, when passed infinity values, it raises `OverflowError` instead. This inconsistency breaks code that catches `ValueError` to handle validation failures. The function correctly raises `ValueError` for NaN and other non-convertible values.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,11 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```