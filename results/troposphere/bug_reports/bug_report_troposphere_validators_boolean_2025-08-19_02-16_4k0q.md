# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 1.0 and 0.0, returning True and False respectively, when it should raise ValueError for non-boolean/integer/string inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Boolean validator should reject all float values."""
    # Skip exact integer floats that are intended to work
    if value == 1.0 or value == 0.0:
        # These incorrectly pass but shouldn't
        try:
            result = boolean(value)
            assert False, f"boolean({value}) should raise ValueError but returned {result}"
        except ValueError:
            pass  # This is what should happen
    elif value in [1, 0]:  # Integer values, not floats
        pass  # These are valid
    else:
        # All other floats should raise ValueError
        try:
            boolean(value)
            assert False, f"boolean({value}) should raise ValueError"
        except ValueError:
            pass  # Expected
```

**Failing input**: `1.0` and `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

# These should raise ValueError but don't
result1 = boolean(1.0)
print(f"boolean(1.0) = {result1}")  # Returns True, should raise ValueError

result2 = boolean(0.0)  
print(f"boolean(0.0) = {result2}")  # Returns False, should raise ValueError

# The bug occurs because Python treats 1.0 == 1 == True and 0.0 == 0 == False
# So when checking 'if x in [True, 1, ...]', float 1.0 matches
```

## Why This Is A Bug

The boolean validator is intended to accept only specific boolean-like values: `True`, `False`, integers `1` and `0`, and strings `"1"`, `"0"`, `"true"`, `"false"`, `"True"`, `"False"`. Float values like `1.0` and `0.0` are not in the documented acceptable inputs but are incorrectly accepted due to Python's equality semantics where `1.0 == 1` and `0.0 == 0`. This violates the validator's contract and could lead to unexpected behavior when users accidentally pass float values.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,6 +36,10 @@ def boolean(x: Literal[False, 0, "false", "False"]) -> Literal[False]: ...
 
 
 def boolean(x: Any) -> bool:
+    # Explicitly reject float values even if they equal 1 or 0
+    if isinstance(x, float) and not isinstance(x, bool):
+        raise ValueError
+    
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
```