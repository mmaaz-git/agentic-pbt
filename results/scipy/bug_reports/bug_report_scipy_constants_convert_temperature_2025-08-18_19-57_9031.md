# Bug Report: scipy.constants.convert_temperature Identity Conversion Introduces Floating-Point Errors

**Target**: `scipy.constants.convert_temperature`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Converting a temperature from a scale to itself (identity conversion) introduces unnecessary floating-point errors instead of returning the exact input value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import scipy.constants as sc

@given(val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_celsius_to_celsius_identity(val):
    """
    Test that converting from Celsius to Celsius returns the same value.
    """
    result = sc.convert_temperature(val, 'Celsius', 'Celsius')
    assert result == val, f"Celsius to Celsius conversion changed value: {val} -> {result}"
```

**Failing input**: `0.99999`

## Reproducing the Bug

```python
import scipy.constants as sc

val = 0.99999
result = sc.convert_temperature(val, 'Celsius', 'Celsius')

print(f"Input: {val}")
print(f"Output: {result}")
print(f"Error: {result - val}")

assert result == val
```

## Why This Is A Bug

Identity conversions (converting from a scale to itself) should be no-ops that return the exact input value. However, the current implementation unnecessarily converts through Kelvin as an intermediate step, introducing floating-point rounding errors. This violates the mathematical identity property f(x) = x when the source and target scales are the same.

## Fix

The function should check if the source and target scales are the same and return the input value directly without any conversions:

```diff
--- a/scipy/constants/_constants.py
+++ b/scipy/constants/_constants.py
@@ -45,6 +45,10 @@ def convert_temperature(
     """
     xp = array_namespace(val)
     _val = _asarray(val, xp=xp, subok=True)
+    
+    # Identity conversion - return input unchanged
+    if old_scale.lower() == new_scale.lower():
+        return _val
+    
     # Convert from `old_scale` to Kelvin
     if old_scale.lower() in ['celsius', 'c']:
         tempo = _val + zero_Celsius
```