# Bug Report: troposphere.validators.boolean Incorrectly Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The boolean validator function incorrectly accepts float values 0.0 and 1.0, treating them as False and True respectively, when it should only accept the specific documented values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.floats())
def test_boolean_validator_rejects_floats(value):
    """Test that boolean validator raises ValueError for all float inputs"""
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result_0 = boolean(0.0)  
print(f"boolean(0.0) = {result_0}")  # Returns False, should raise ValueError

result_1 = boolean(1.0)
print(f"boolean(1.0) = {result_1}")  # Returns True, should raise ValueError

print(f"\nRoot cause: 0.0 in [0, False] = {0.0 in [0, False]}")  # True
print(f"Root cause: 1.0 in [1, True] = {1.0 in [1, True]}")  # True
```

## Why This Is A Bug

The boolean validator's implementation uses Python's `in` operator to check if a value matches the allowed list. However, Python considers `0.0 == 0` and `1.0 == 1` as True, causing unintended float acceptance. The function should only accept the explicitly documented values: `True, 1, "1", "true", "True"` for true values and `False, 0, "0", "false", "False"` for false values.

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