# Bug Report: troposphere.validators.boolean Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept boolean, integer (0/1), and string representations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects float inputs"""
    from troposphere.validators import boolean
    
    # Boolean validator should only accept bool, int 0/1, and strings
    # It should reject all float values
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

print(f"boolean(0.0) = {boolean(0.0)}")  # Returns False, should raise ValueError
print(f"boolean(1.0) = {boolean(1.0)}")  # Returns True, should raise ValueError
print(f"boolean(2.0) = {boolean(2.0)}")  # Correctly raises ValueError
```

## Why This Is A Bug

The boolean validator's implementation uses Python's `in` operator to check membership in lists like `[True, 1, "1", "true", "True"]`. Due to Python's numeric type coercion, `0.0 == 0` and `1.0 == 1` evaluate to True, causing `0.0 in [0]` and `1.0 in [1]` to also return True. This allows float values to pass validation when they shouldn't, violating the validator's contract of accepting only booleans, specific integers (0/1), and their string representations.

This affects all CloudFormation resources using boolean properties across 30+ modules in troposphere, potentially allowing invalid CloudFormation templates to be generated when users accidentally pass float values.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,6 +37,10 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
+    # Explicitly reject float types (except for bool which is a subclass of int)
+    if isinstance(x, float) and not isinstance(x, bool):
+        raise ValueError
+    
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
```