# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` validator function incorrectly accepts float values `0.0` and `1.0`, converting them to boolean values instead of raising a ValueError as intended.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(value=st.floats())
def test_boolean_validator_rejects_floats(value):
    try:
        boolean(value)
        assert False, f"Expected ValueError for float {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result1 = boolean(0.0)
print(f"boolean(0.0) = {result1}")  # Returns False, should raise ValueError

result2 = boolean(1.0)  
print(f"boolean(1.0) = {result2}")  # Returns True, should raise ValueError
```

## Why This Is A Bug

The `boolean` validator is explicitly designed to accept only specific values: `True`, `False`, `1`, `0`, and their string representations. The function uses equality checks (`x in [...]`) which should reject floats. However, Python's equality comparison `0.0 == 0` and `1.0 == 1` returns `True`, causing floats to be incorrectly accepted. This violates the validator's intended contract of strict type checking.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,8 +37,10 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
+    if isinstance(x, float):
+        raise ValueError
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```