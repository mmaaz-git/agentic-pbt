# Bug Report: troposphere.validators Type Preservation Bug

**Target**: `troposphere.validators.integer` and `troposphere.validators.double`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` and `double` validators do not convert string inputs to their respective numeric types, causing type inconsistency in properties and potential TypeError exceptions during comparisons.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer, double

@given(st.text(min_size=1).filter(lambda s: s.replace('-', '').isdigit()))
def test_validator_type_conversion(s):
    """Validators should convert string inputs to appropriate numeric types."""
    result = integer(s)
    assert isinstance(result, int), f"Integer validator didn't convert string '{s}' to int, got {type(result)}"
```

**Failing input**: `'0'`

## Reproducing the Bug

```python
from troposphere.validators import integer, double
from troposphere.inspectorv2 import PortRangeFilter

# Bug 1: Validators preserve input type
result = integer("42")
print(f"integer('42') = {result!r}, type = {type(result)}")  # Returns '42' (str), not 42 (int)

result = double("42.5")
print(f"double('42.5') = {result!r}, type = {type(result)}")  # Returns '42.5' (str), not 42.5 (float)

# Bug 2: Causes mixed types in properties
prf = PortRangeFilter(BeginInclusive="80", EndInclusive=443)
print(prf.properties)  # {'BeginInclusive': '80', 'EndInclusive': 443}

# Bug 3: Mixed types cause TypeError
prf2 = PortRangeFilter(BeginInclusive="100", EndInclusive=99)
try:
    if prf2.properties['BeginInclusive'] > prf2.properties['EndInclusive']:
        pass
except TypeError as e:
    print(f"TypeError: {e}")  # '>' not supported between instances of 'str' and 'int'
```

## Why This Is A Bug

The validators are named `integer` and `double`, implying they should ensure the values are of the correct numeric type. However, they only validate that the input CAN be converted but return the original value unchanged. This violates the contract implied by the validator names and causes type inconsistency issues.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,10 +46,10 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        return int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
-    else:
-        return x
 
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
@@ -93,10 +93,10 @@ def integer_list_item_checker(
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        float(x)
+        return float(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
-    else:
-        return x
```