# Bug Report: troposphere.timestream.boolean() Incorrectly Accepts Float Values

**Target**: `troposphere.timestream.boolean`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean()` validation function incorrectly accepts float values `0.0` and `1.0`, returning `False` and `True` respectively, when it should raise `ValueError` for all non-boolean/integer/string inputs.

## Property-Based Test

```python
@given(st.floats())
def test_boolean_rejects_all_floats(value):
    """Test that boolean() raises ValueError for all float inputs."""
    with pytest.raises(ValueError):
        ts.boolean(value)
```

**Failing input**: `0.0` and `1.0`

## Reproducing the Bug

```python
import troposphere.timestream as ts

result1 = ts.boolean(0.0)
print(f"boolean(0.0) = {result1}")

result2 = ts.boolean(1.0)  
print(f"boolean(1.0) = {result2}")

try:
    result3 = ts.boolean(0.5)
except ValueError:
    print("boolean(0.5) correctly raised ValueError")
```

## Why This Is A Bug

The function's implementation checks if the input is in lists containing specific values: `[True, 1, "1", "true", "True"]` and `[False, 0, "0", "false", "False"]`. However, Python's `in` operator uses equality comparison, and `0.0 == 0` and `1.0 == 1` evaluate to `True`. This allows float values to pass validation when they shouldn't, violating the function's contract to only accept boolean values, integers 0/1, or specific string representations.

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