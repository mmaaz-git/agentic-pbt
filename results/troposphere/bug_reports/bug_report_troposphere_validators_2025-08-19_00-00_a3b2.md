# Bug Report: troposphere.validators Boolean and Integer Validation Flaws

**Target**: `troposphere.validators.boolean` and `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean()` validator incorrectly accepts float values 0.0 and 1.0, and the `integer()` validator accepts non-integer float values without proper validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean, integer

@given(st.floats())
def test_boolean_validator_should_reject_floats(value):
    """boolean() should reject all float inputs"""
    with pytest.raises(ValueError):
        boolean(value)

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_floats(value):
    """integer() should reject non-integer floats"""
    if not value.is_integer():
        with pytest.raises(ValueError):
            integer(value)
```

**Failing input**: `boolean(0.0)` returns `False`, `boolean(1.0)` returns `True`, `integer(0.5)` returns `0.5`

## Reproducing the Bug

```python
from troposphere.validators import boolean, integer

# Bug 1: boolean() accepts floats 0.0 and 1.0
assert boolean(0.0) == False  # Should raise ValueError
assert boolean(1.0) == True   # Should raise ValueError

# Bug 2: integer() accepts non-integer floats
assert integer(0.5) == 0.5    # Should raise ValueError
assert integer(3.14) == 3.14  # Should raise ValueError
```

## Why This Is A Bug

The validators are meant to enforce strict type checking for CloudFormation properties. Accepting float values when only booleans or integers are expected violates the type contract and could lead to unexpected CloudFormation template behavior. The docstrings and type hints indicate these validators should be strict about their input types.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,10 +36,14 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    # Use strict type checking to avoid float equality issues
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
 
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check that conversion doesn't lose precision for floats
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("Float value %r is not an integer" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```