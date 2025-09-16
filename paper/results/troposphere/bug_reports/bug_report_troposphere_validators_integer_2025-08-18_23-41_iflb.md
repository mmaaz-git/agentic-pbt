# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Float Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `integer()` validator incorrectly accepts float values like 1.5, which are not integers, silently allowing data loss when converted to int.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_rejects_non_integer_floats(value):
    """Integer validator should reject floats that are not whole numbers"""
    try:
        result = integer(value)
        # Bug: Non-integer float was accepted
        assert False, f"Float {value} should not be accepted as integer, returned {result}"
    except ValueError:
        pass  # Expected behavior
```

**Failing input**: `1.5`, `2.7`, `-3.14`, etc.

## Reproducing the Bug

```python
from troposphere.validators import integer

# These floats are not integers but are incorrectly accepted
result1 = integer(1.5)   # Returns 1.5 (incorrect - should raise ValueError)
result2 = integer(2.7)   # Returns 2.7 (incorrect - should raise ValueError)
result3 = integer(-3.14) # Returns -3.14 (incorrect - should raise ValueError)

print(f"integer(1.5) = {result1}, int(result1) = {int(result1)}")
print(f"integer(2.7) = {result2}, int(result2) = {int(result2)}")
print(f"integer(-3.14) = {result3}, int(result3) = {int(result3)}")

# This shows data loss - 1.5 becomes 1 when converted
# The validator should reject non-integer values upfront
```

## Why This Is A Bug

The `integer()` validator is supposed to validate that a value can be safely used as an integer in CloudFormation templates. The current implementation only checks if `int(x)` doesn't raise an exception, but this is insufficient. Float values like 1.5 can be converted to int (resulting in 1), but they are not integers. This can lead to silent data loss and unexpected behavior when users pass float values expecting them to be rejected. The validator should ensure the value is actually an integer or a string representation of an integer, not just something convertible to int.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,13 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
-    except (ValueError, TypeError):
+        int_val = int(x)
+        # Check if conversion loses precision (for floats)
+        if isinstance(x, float):
+            if x != int_val:
+                raise ValueError("%r is not a valid integer (has decimal part)" % x)
+    except (ValueError, TypeError) as e:
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```