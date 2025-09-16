# Bug Report: troposphere.validators.ec2 validate_int_to_str Inconsistent Error Types

**Target**: `troposphere.validators.ec2.validate_int_to_str`
**Severity**: Low  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate_int_to_str` function raises ValueError for invalid string inputs instead of the expected TypeError, causing inconsistent error handling behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators.ec2 import validate_int_to_str

@given(st.text())
def test_validate_int_to_str_str_input(s):
    """Property: validate_int_to_str should handle valid numeric strings"""
    try:
        int_val = int(s)
        result = validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
    except (ValueError, TypeError):
        with pytest.raises(TypeError):
            validate_int_to_str(s)
```

**Failing input**: `""` (empty string)

## Reproducing the Bug

```python
from troposphere.validators.ec2 import validate_int_to_str

validate_int_to_str("")
```

## Why This Is A Bug

The function is designed to accept only int or str types and raise TypeError for invalid types. However, when given a string that cannot be converted to an integer (like empty string, "abc", or "12.34"), it raises ValueError from the `int()` conversion instead of the intended TypeError. This creates inconsistent error handling where some invalid inputs raise TypeError (e.g., None, lists, dicts) while others raise ValueError (invalid strings).

## Fix

```diff
--- a/troposphere/validators/ec2.py
+++ b/troposphere/validators/ec2.py
@@ -54,7 +54,10 @@ def validate_int_to_str(x):
     if isinstance(x, int):
         return str(x)
     if isinstance(x, str):
-        return str(int(x))
+        try:
+            return str(int(x))
+        except ValueError:
+            raise TypeError(f"Value {x} of type {type(x)} must be either int or str")
 
     raise TypeError(f"Value {x} of type {type(x)} must be either int or str")
```