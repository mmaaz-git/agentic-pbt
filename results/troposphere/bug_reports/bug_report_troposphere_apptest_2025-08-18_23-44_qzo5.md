# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `boolean` validator function incorrectly accepts float values 0.0 and 1.0, returning False and True respectively, when it should raise a ValueError for all float inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_raises_on_float(value):
    """Test that float values raise ValueError as documented"""
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0` (also `1.0`)

## Reproducing the Bug

```python
from troposphere.validators import boolean

print(boolean(0.0))  
print(boolean(1.0))  
print(boolean(-0.0)) 
```

## Why This Is A Bug

The `boolean` function is designed to strictly validate boolean-like inputs for AWS CloudFormation templates. According to its implementation (lines 39-43 in validators/__init__.py), it should only accept:
- True values: `True`, `1`, `"1"`, `"true"`, `"True"`  
- False values: `False`, `0`, `"0"`, `"false"`, `"False"`

Any other input should raise a ValueError. However, due to Python's equality comparison (`0.0 == 0` returns `True`), the function incorrectly accepts float values 0.0 and 1.0 when using the `in` operator to check membership in the validation lists.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,9 +37,9 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```