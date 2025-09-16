# Bug Report: troposphere.validators Boolean Validator Accepts Float Values

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept the documented integer and string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest

invalid_bool_strategy = st.one_of(
    st.floats(),
    st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.integers().filter(lambda x: x not in [0, 1])
)

@given(invalid_bool_strategy)
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        boolean(value)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import boolean

result = boolean(0.0)
print(f"boolean(0.0) = {result}")  # False
print(f"type: {type(result)}")      # <class 'bool'>

result = boolean(1.0)  
print(f"boolean(1.0) = {result}")  # True
```

## Why This Is A Bug

The boolean validator documentation and type hints indicate it should only accept:
- Boolean values: True, False
- Integer values: 0, 1  
- String values: "0", "1", "true", "false", "True", "False"

Accepting float values violates the validator's contract. The issue occurs because Python's `in` operator considers `0.0 == 0` and `1.0 == 1` as True, causing unintended float-to-boolean conversion.

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