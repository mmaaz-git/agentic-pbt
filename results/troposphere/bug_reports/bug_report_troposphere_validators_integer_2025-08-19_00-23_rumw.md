# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator function incorrectly accepts float values with decimal parts (e.g., 10.5, 3.14) as valid integers, violating its intended validation purpose.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False)
       .filter(lambda x: x != int(x)))
def test_integer_rejects_non_integers(value):
    """
    Property: The integer() validator should reject any float that is not 
    equal to its integer conversion (i.e., has a fractional part).
    """
    try:
        result = integer(value)
        assert False, f"integer({value}) should raise ValueError but returned {result}"
    except ValueError:
        pass
```

**Failing input**: `10.5` (or any float with decimal part)

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(10.5)
print(f"integer(10.5) = {result}")

result2 = integer(3.14)
print(f"integer(3.14) = {result2}")

result3 = integer(-2.7)
print(f"integer(-2.7) = {result3}")
```

## Why This Is A Bug

The `integer()` validator is meant to validate that a value is a valid integer. However, it currently accepts any value for which `int(x)` doesn't raise an exception. Since `int(10.5)` returns `10` without error, the validator incorrectly accepts `10.5` as valid and returns it unchanged. This violates the expected contract that only actual integer values should pass validation.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,7 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        if isinstance(x, float) and x != int(x):
+            raise ValueError("%r is not a valid integer" % x)
+        int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```