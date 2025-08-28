# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept the documented boolean-like values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators as validators

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects all float inputs."""
    try:
        validators.boolean(value)
        assert False, f"Should have raised ValueError for float {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import troposphere.validators as validators

result1 = validators.boolean(0.0)
print(f"boolean(0.0) = {result1}")  # Returns False, should raise ValueError

result2 = validators.boolean(1.0)  
print(f"boolean(1.0) = {result2}")  # Returns True, should raise ValueError
```

## Why This Is A Bug

The boolean validator's documented behavior is to accept specific values: `True, 1, "1", "true", "True"` for true and `False, 0, "0", "false", "False"` for false. However, due to Python's equality comparison where `1.0 == 1` and `0.0 == 0`, the validator unintentionally accepts float values. This violates the type contract and could lead to unexpected behavior when float values are passed where only boolean-like values are expected.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,10 +36,10 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```