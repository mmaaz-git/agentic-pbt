# Bug Report: troposphere.validators.boolean Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `boolean` validator function incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept the documented types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import boolean

@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "false", "True", "False"]),
    st.floats(),
    st.none()
))
def test_boolean_validator_invalid_inputs(value):
    """Boolean validator should raise ValueError for invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result1 = boolean(0.0)
print(f"boolean(0.0) = {result1}")  

result2 = boolean(1.0)
print(f"boolean(1.0) = {result2}")

result3 = boolean(2.0)
print(f"boolean(2.0) = {result3}")
```

## Why This Is A Bug

The boolean validator's documented behavior states it should accept:
- True values: `True`, `1`, `"1"`, `"true"`, `"True"`
- False values: `False`, `0`, `"0"`, `"false"`, `"False"`

However, due to Python's equality behavior where `0.0 == 0` and `1.0 == 1`, the function incorrectly accepts float values. This violates the API contract and could lead to unexpected behavior when float values are passed where only boolean-like values are expected.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if type(x) in [bool, int, str] and x in [True, 1, "1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in [bool, int, str] and x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```