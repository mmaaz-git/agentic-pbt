# Bug Report: troposphere.serverless.boolean() Accepts Float Values

**Target**: `troposphere.serverless.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean()` function incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, when it should only accept the documented set of values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import troposphere.serverless as serverless

@given(st.floats())
def test_boolean_rejects_floats(value):
    """Test that boolean() rejects all float inputs."""
    with pytest.raises(ValueError):
        serverless.boolean(value)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
import troposphere.serverless as serverless

result1 = serverless.boolean(0.0)
print(f"boolean(0.0) = {result1}")

result2 = serverless.boolean(1.0)
print(f"boolean(1.0) = {result2}")
```

## Why This Is A Bug

The `boolean()` function is documented to accept only specific values: `True, 1, "1", "true", "True"` for truthy and `False, 0, "0", "false", "False"` for falsy. It should raise ValueError for any other input. However, due to Python's equality comparison (`0.0 == 0` is True), the function incorrectly accepts float values 0.0 and 1.0.

## Fix

```diff
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) == int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) == int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```