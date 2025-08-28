# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator accepts float values 0.0 and 1.0, converting them to False and True respectively, which violates the expected contract of accepting only specific boolean representations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(x):
    """Test that boolean validator rejects float values"""
    with pytest.raises(ValueError):
        boolean(x)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result = boolean(0.0)
print(f"boolean(0.0) = {result}")  # Returns False

result = boolean(1.0)
print(f"boolean(1.0) = {result}")  # Returns True

result = boolean(-0.0)
print(f"boolean(-0.0) = {result}")  # Returns False
```

## Why This Is A Bug

The boolean validator explicitly checks for specific values: `[True, 1, "1", "true", "True"]` for true and `[False, 0, "0", "false", "False"]` for false. However, it uses the `in` operator which performs equality comparison, and in Python `0.0 == 0` and `1.0 == 1` evaluate to True. This causes:

1. Unexpected acceptance of float values when only boolean/integer/string values are intended
2. Potential type confusion in CloudFormation templates
3. Inconsistent behavior (2.0 is rejected but 1.0 is accepted)

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,9 +37,9 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or (isinstance(x, int) and x == 1) or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or (isinstance(x, int) and x == 0) or x in ["0", "false", "False"]:
         return False
     raise ValueError
```