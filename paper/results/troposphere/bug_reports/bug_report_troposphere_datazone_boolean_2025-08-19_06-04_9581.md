# Bug Report: troposphere.datazone.boolean() Incorrectly Accepts Float Values

**Target**: `troposphere.datazone.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean()` function incorrectly accepts float values `0.0` and `1.0`, returning `False` and `True` respectively, when it should raise `ValueError` for all float inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import troposphere.datazone as dz

@given(st.floats())
def test_boolean_should_reject_all_floats(value):
    """Test that boolean() raises ValueError for all float inputs"""
    with pytest.raises(ValueError):
        dz.boolean(value)
```

**Failing input**: `0.0` (also fails with `1.0`)

## Reproducing the Bug

```python
import troposphere.datazone as dz

result1 = dz.boolean(0.0)
print(f"boolean(0.0) = {result1}")  # Returns False

result2 = dz.boolean(1.0)  
print(f"boolean(1.0) = {result2}")  # Returns True
```

## Why This Is A Bug

The function is documented to accept only specific values: `True`, `1`, `"1"`, `"true"`, `"True"` for true values, and `False`, `0`, `"0"`, `"false"`, `"False"` for false values. All other inputs should raise `ValueError`. The bug occurs because Python's `in` operator uses equality comparison, and `0.0 == 0` and `1.0 == 1` evaluate to `True`, causing floats to be incorrectly accepted.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
        return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
        return False
    raise ValueError
```