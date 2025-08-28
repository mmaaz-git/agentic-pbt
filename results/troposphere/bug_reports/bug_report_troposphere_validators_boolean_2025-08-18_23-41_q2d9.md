# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `boolean()` validator incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept specific integer, boolean, and string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats(allow_nan=False))
def test_boolean_rejects_float_values(value):
    """Boolean validator should reject all float values"""
    if value not in [0.0, 1.0]:
        with pytest.raises(ValueError):
            boolean(value)
    else:
        # Bug: 0.0 and 1.0 are incorrectly accepted
        result = boolean(value)
        assert False, f"Float {value} should not be accepted but returned {result}"
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

# These should raise ValueError but don't
result1 = boolean(0.0)  # Returns False (incorrect)
result2 = boolean(1.0)  # Returns True (incorrect)

print(f"boolean(0.0) = {result1}")  # False
print(f"boolean(1.0) = {result2}")  # True

# Correct behavior for comparison
try:
    boolean(2.0)  # Correctly raises ValueError
except ValueError:
    print("boolean(2.0) correctly raises ValueError")
```

## Why This Is A Bug

The boolean validator's docstring and implementation suggest it should only accept specific values: `True`, `1`, `"1"`, `"true"`, `"True"` for truthy values and `False`, `0`, `"0"`, `"false"`, `"False"` for falsy values. The validator uses the `in` operator with lists containing integers, which causes Python to treat `0.0 == 0` and `1.0 == 1` as True. This violates the type contract - floats should not be valid boolean inputs in a CloudFormation context.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,10 +37,12 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    # Check exact type to avoid float values like 1.0 being accepted
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```