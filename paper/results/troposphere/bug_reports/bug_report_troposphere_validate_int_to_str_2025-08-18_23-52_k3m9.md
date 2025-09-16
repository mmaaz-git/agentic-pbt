# Bug Report: troposphere.validators.autoscaling.validate_int_to_str Raises Wrong Exception Type

**Target**: `troposphere.validators.autoscaling.validate_int_to_str`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `validate_int_to_str` function raises `ValueError` instead of `TypeError` when given a non-numeric string, violating its documented contract behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators.autoscaling import validate_int_to_str

@given(st.one_of(
    st.integers(),
    st.text(min_size=1),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_validate_int_to_str(value):
    """Test backward compatibility function for int/str conversion"""
    
    if isinstance(value, int):
        result = validate_int_to_str(value)
        assert result == str(value)
    elif isinstance(value, str):
        try:
            int_val = int(value)
            result = validate_int_to_str(value)
            assert result == str(int_val)
        except (ValueError, TypeError):
            # Should raise TypeError for non-numeric strings
            with pytest.raises(TypeError):
                validate_int_to_str(value)
    else:
        # All other types should raise TypeError
        with pytest.raises(TypeError):
            validate_int_to_str(value)
```

**Failing input**: `':'`

## Reproducing the Bug

```python
from troposphere.validators.autoscaling import validate_int_to_str

result = validate_int_to_str(':')
```

## Why This Is A Bug

The function is designed to handle backward compatibility between int and str types. According to its implementation pattern and error message format, it should raise `TypeError` for values that are not int or valid numeric strings (consistent with line 39: `raise TypeError(f"Value {x} of type {type(x)} must be either int or str")`). However, when given a non-numeric string like `':'`, it raises `ValueError` instead because the `int()` conversion on line 37 is not wrapped in proper exception handling.

## Fix

```diff
--- a/troposphere/validators/autoscaling.py
+++ b/troposphere/validators/autoscaling.py
@@ -34,7 +34,10 @@ def validate_int_to_str(x):
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