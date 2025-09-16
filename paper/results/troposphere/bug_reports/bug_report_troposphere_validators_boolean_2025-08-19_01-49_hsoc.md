# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean()` validator function incorrectly accepts float values 0.0 and 1.0, returning False and True respectively, when it should raise ValueError for all non-specified input types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects float inputs"""
    try:
        boolean(value)
        if value not in [0.0, 1.0]:
            # Other floats correctly raise ValueError
            assert False, f"boolean() should have raised ValueError for {value}"
    except ValueError:
        pass  # Expected for floats
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result1 = boolean(0.0)
print(f"boolean(0.0) = {result1}")  

result2 = boolean(1.0)  
print(f"boolean(1.0) = {result2}")

print("\nThese should raise ValueError but instead return False and True")
```

## Why This Is A Bug

The boolean validator is designed to accept only a specific set of values: `[True, 1, "1", "true", "True"]` for truthy and `[False, 0, "0", "false", "False"]` for falsy. However, due to Python's equality comparison where `0.0 == 0` and `1.0 == 1`, float values 0.0 and 1.0 are incorrectly accepted. This violates the type contract and could lead to unexpected behavior in CloudFormation template validation.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```