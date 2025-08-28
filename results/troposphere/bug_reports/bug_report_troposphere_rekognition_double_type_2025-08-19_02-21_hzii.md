# Bug Report: troposphere.rekognition double Function Returns Wrong Type

**Target**: `troposphere.rekognition.double`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double` function returns a string when given a string input, but should return a float to maintain type consistency.

## Property-Based Test

```python
import math
from hypothesis import given, strategies as st
import troposphere.rekognition as rek

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_double_string_round_trip(value):
    """Test that double function correctly handles string representations"""
    str_value = str(value)
    result = rek.double(str_value)
    assert math.isclose(result, value, rel_tol=1e-9, abs_tol=1e-10)
```

**Failing input**: `"0.0"` (or any string representation of a number)

## Reproducing the Bug

```python
import troposphere.rekognition as rek

result = rek.double("2.5")
print(f"double('2.5') = {result}")
print(f"Type: {type(result)}")
print(f"Expected: <class 'float'>, Got: {type(result)}")

# This causes type errors when the result is used in float operations
import math
math.isclose(result, 2.5)  # TypeError: must be real number, not str
```

## Why This Is A Bug

The `double` function is used for property validation expecting float values. When it returns a string instead of a float, it breaks type expectations and causes downstream errors in code that expects numeric operations.

## Fix

Convert string inputs to float before returning:

```diff
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        return float(x)
+        result = float(x)
+        return result
     except (ValueError, TypeError):
         raise ValueError(f"{x} is not a valid double")
```