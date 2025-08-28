# Bug Report: troposphere.stepfunctions.boolean Accepts Float Values

**Target**: `troposphere.stepfunctions.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean()` function incorrectly accepts float values 0.0 and 1.0, converting them to False and True respectively, while rejecting other float values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.stepfunctions as sf

@given(st.floats())
def test_boolean_should_reject_all_floats(x):
    """Test that boolean() raises ValueError for all float inputs."""
    try:
        sf.boolean(x)
        assert False, f"Expected ValueError for float input {x}"
    except ValueError:
        pass  # Expected
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import troposphere.stepfunctions as sf

result1 = sf.boolean(0.0)
print(f"boolean(0.0) = {result1}")

result2 = sf.boolean(1.0)  
print(f"boolean(1.0) = {result2}")

try:
    sf.boolean(2.0)
except ValueError:
    print("boolean(2.0) raises ValueError as expected")
```

## Why This Is A Bug

The boolean validator is used for CloudFormation boolean properties (like `TracingConfiguration.Enabled` and `LoggingConfiguration.IncludeExecutionData`). It should only accept explicit boolean values and their string representations ("true", "false", etc.), not numeric floats. The current behavior is inconsistent: it accepts 0.0 and 1.0 but rejects other floats like 2.0 or 0.5.

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