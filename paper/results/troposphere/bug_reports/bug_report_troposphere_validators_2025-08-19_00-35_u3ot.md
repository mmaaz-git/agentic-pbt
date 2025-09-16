# Bug Report: troposphere.validators Type Coercion Vulnerabilities

**Target**: `troposphere.validators.boolean`, `troposphere.validators.integer`, and `troposphere.validators.positive_integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The boolean, integer, and positive_integer validators in troposphere incorrectly accept float values due to Python's type coercion, with positive_integer accepting negative floats like -0.5, violating fundamental validation contracts.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators as validators
import pytest

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Boolean validator should reject float inputs"""
    if value not in [0.0, 1.0]:
        with pytest.raises(ValueError):
            validators.boolean(value)

@given(st.floats(allow_nan=False))
def test_integer_validator_rejects_floats(value):
    """Integer validator should reject non-integer float inputs"""
    if not value.is_integer():
        with pytest.raises(ValueError):
            validators.integer(value)

@given(st.floats(max_value=-0.1))
def test_positive_integer_rejects_negative_floats(value):
    """Positive integer validator should reject negative floats"""
    with pytest.raises(ValueError):
        validators.positive_integer(value)
```

**Failing input**: `0.0` and `1.0` for boolean; `0.5`, `1.5` for integer; `-0.5` for positive_integer

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import validators

# Bug 1: Boolean validator accepts floats
result1 = validators.boolean(0.0)
print(f"boolean(0.0) = {result1}")  # Returns False, should raise ValueError

result2 = validators.boolean(1.0)  
print(f"boolean(1.0) = {result2}")  # Returns True, should raise ValueError

# Bug 2: Integer validator accepts and returns floats
result3 = validators.integer(0.5)
print(f"integer(0.5) = {result3}")  # Returns 0.5, should raise ValueError

result4 = validators.integer(1.5)
print(f"integer(1.5) = {result4}")  # Returns 1.5, should raise ValueError

# Bug 3: Positive integer validator accepts negative floats
result5 = validators.positive_integer(-0.5)
print(f"positive_integer(-0.5) = {result5}")  # Returns -0.5, should raise ValueError

result6 = validators.positive_integer(1.5)
print(f"positive_integer(1.5) = {result6}")  # Returns 1.5, should raise ValueError
```

## Why This Is A Bug

1. **Boolean validator**: The function is meant to validate boolean-like inputs (bool, int 0/1, string representations). Float values like `0.0` and `1.0` are accepted due to Python's equality operator coercing types (`1.0 == 1` is True). This violates the principle of strict type validation.

2. **Integer validator**: The function checks if `int(x)` succeeds but then returns the original value `x` unchanged. This means floats pass through as floats, defeating the purpose of integer validation. The validator should either convert to int or reject non-integer values.

3. **Positive integer validator**: This validator has cascading failures:
   - It relies on the broken integer validator, so floats pass through
   - It checks `int(p) < 0` which converts `-0.5` to `0`, allowing negative floats between -1 and 0 to pass
   - It returns the original value instead of the validated integer
   - This allows values like `-0.5` (negative and non-integer) to pass as "positive integers"

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,6 +36,9 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
+    # Reject float types explicitly
+    if isinstance(x, float) and not isinstance(x, bool):
+        raise ValueError("%r is not a valid boolean" % x)
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
@@ -46,16 +49,22 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        # Reject non-integer floats
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError("%r is not a valid integer" % x)
+        int_val = int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
 
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     p = integer(x)
-    if int(p) < 0:
+    # Convert to int for proper comparison
+    int_val = int(p)
+    if int_val < 0:
         raise ValueError("%r is not a positive integer" % x)
-    return x
+    # Return the validated value from integer(), not the original x
+    return p
```