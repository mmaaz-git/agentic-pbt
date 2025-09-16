# Bug Report: troposphere.ram.boolean Accepts Float Values

**Target**: `troposphere.ram.boolean`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` function unintentionally accepts float values 0.0 and 1.0, converting them to boolean values, when it should only accept bool, int (0/1), and specific string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ram as ram
import pytest

@given(st.floats())
def test_boolean_accepts_floats_unexpectedly(f):
    """The boolean function should not accept float values"""
    if f == 0.0 or f == 1.0:
        # These floats are accepted but shouldn't be
        result = ram.boolean(f)
        assert isinstance(result, bool)
        assert (f == 0.0 and result == False) or (f == 1.0 and result == True)
    else:
        # Other floats correctly raise ValueError
        with pytest.raises(ValueError):
            ram.boolean(f)
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import troposphere.ram as ram

# These should raise ValueError but don't
print(ram.boolean(0.0))  # Returns False
print(ram.boolean(1.0))  # Returns True
print(ram.boolean(-0.0)) # Returns False

# This can lead to unexpected behavior
rs = ram.ResourceShare('TestShare')
rs.Name = 'MyShare'
rs.AllowExternalPrincipals = 1.0  # Float accepted, should probably error
print(rs.to_dict()['Properties']['AllowExternalPrincipals'])  # True
```

## Why This Is A Bug

The function is designed to validate boolean-like inputs for CloudFormation templates. The accepted values are explicitly listed as `[True, 1, "1", "true", "True"]` and `[False, 0, "0", "false", "False"]`. Float values are not intended inputs, but due to Python's `==` operator treating `0.0 == 0` and `1.0 == 1` as True, these floats slip through. This could lead to subtle bugs where float values are silently converted to booleans instead of raising an error.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if type(x) in (bool, int, str) and x in [True, 1, "1", "true", "True"]:
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in (bool, int, str) and x in [False, 0, "0", "false", "False"]:
        return False
    raise ValueError
```