# Bug Report: troposphere.timestream.integer() Incorrectly Accepts Float Values

**Target**: `troposphere.timestream.integer`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts float values without raising `ValueError`, returning the float value unchanged when it should only accept integers or integer-convertible strings.

## Property-Based Test

```python
@given(st.floats().filter(lambda x: not x.is_integer()))
def test_integer_rejects_non_integer_floats(value):
    """Test that integer() raises ValueError for non-integer float inputs."""
    with pytest.raises(ValueError):
        ts.integer(value)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import troposphere.timestream as ts

result = ts.integer(0.5)
print(f"integer(0.5) = {result}")
print(f"Type of result: {type(result)}")

result2 = ts.integer(3.14)
print(f"integer(3.14) = {result2}")
```

## Why This Is A Bug

The function's name and type signature suggest it validates integer values, but it accepts any value that can be converted to int without raising an exception. Python's `int()` function successfully converts floats by truncating them, so `int(0.5)` returns `0` without error. The `integer()` function then returns the original float value `0.5`, which violates the expectation that this function validates and returns integer values.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError
+        int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```