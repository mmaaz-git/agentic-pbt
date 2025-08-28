# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 0.0 and 1.0 when it should only accept specific integer and string representations of boolean values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator rejects float values."""
    try:
        boolean(value)
        assert False, f"boolean() should have raised ValueError for float {value}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

result = boolean(0.0)
print(f"boolean(0.0) = {result}")  # Returns False, should raise ValueError

result = boolean(1.0)  
print(f"boolean(1.0) = {result}")  # Returns True, should raise ValueError
```

## Why This Is A Bug

The boolean validator's implementation explicitly checks if the input value is in specific lists: `[True, 1, "1", "true", "True"]` for truthy values and `[False, 0, "0", "false", "False"]` for falsy values. Floats are not included in these lists, but due to Python's equality semantics where `0.0 == 0` and `1.0 == 1`, float values 0.0 and 1.0 incorrectly pass validation. This violates the function's contract which should only accept the documented boolean representations.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -37,10 +37,12 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    # Check type explicitly to avoid float 1.0 matching integer 1
+    if type(x) in (bool, int, str) and x in [True, 1, "1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in (bool, int, str) and x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```