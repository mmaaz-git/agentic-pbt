# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values like 0.0 and 1.0 as valid boolean inputs, violating its documented contract of only accepting specific boolean-like values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects float inputs"""
    if value not in [0.0, 1.0]:  # Skip non-problematic floats
        return
    with pytest.raises(ValueError):
        boolean(value)
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

The boolean validator is documented to accept only specific values: `True`, `1`, `"1"`, `"true"`, `"True"` for true values and `False`, `0`, `"0"`, `"false"`, `"False"` for false values. The implementation uses `x in [False, 0, ...]` which inadvertently allows float values because Python evaluates `0.0 == 0` as `True`. This violates the API contract and could lead to unexpected behavior when float values are passed where strict boolean validation is expected.

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