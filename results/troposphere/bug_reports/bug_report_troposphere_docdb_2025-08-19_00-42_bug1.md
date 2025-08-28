# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` validator function accepts float values with non-zero fractional parts (e.g., 42.7), violating the expectation that it should only validate integer values.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import math
from troposphere import validators

@given(st.floats(allow_nan=False, allow_infinity=False))
@example(42.7)
def test_integer_validator_property(x):
    """Integer validator should only accept values where int(x) == x"""
    try:
        result = validators.integer(x)
        if not math.isclose(x, int(x)):
            raise AssertionError(f"integer({x}) accepted non-integer value")
    except ValueError:
        pass  # Correctly rejected non-integer
```

**Failing input**: `42.7`

## Reproducing the Bug

```python
from troposphere import validators

result = validators.integer(42.7)
print(f"Result: {result}")  # Output: 42.7
print(f"Type: {type(result)}")  # Output: <class 'float'>
```

## Why This Is A Bug

The function is named `integer()` and its purpose is to validate integer inputs. Accepting float values with decimal parts violates this contract. The function performs `int(x)` to check if conversion is possible but doesn't verify that the value is actually an integer (no fractional part).

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check if the value is actually an integer (no fractional part)
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
```