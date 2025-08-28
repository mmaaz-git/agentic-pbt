# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator accepts non-integer float values like 42.5, violating the semantic contract that an "integer" validator should only accept whole numbers.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_rejects_non_integers(x):
    """Integer validator should reject non-integer floats."""
    assume(x != int(x))  # Only test non-integer floats
    
    try:
        result = integer(x)
        # If this doesn't raise an error, it's a bug
        assert False, f"Integer validator accepted non-integer {x}"
    except ValueError:
        pass  # Expected behavior
```

**Failing input**: `x=42.5`

## Reproducing the Bug

```python
from troposphere.validators import integer
from troposphere.inspectorv2 import PortRangeFilter

# Bug 1: Integer validator accepts non-integer floats
result = integer(42.5)
print(f"integer(42.5) = {result}")  # Returns 42.5, should raise ValueError

result = integer(42.9)
print(f"integer(42.9) = {result}")  # Returns 42.9, should raise ValueError

# Bug 2: PortRangeFilter accepts non-integer port numbers
prf = PortRangeFilter(BeginInclusive=80.5, EndInclusive=443.9)
print(prf.properties)  # {'BeginInclusive': 80.5, 'EndInclusive': 443.9}
# Port numbers must be integers - you can't bind to port 80.5
```

## Why This Is A Bug

An "integer" validator should only accept whole numbers. Accepting floats like 42.5 violates the semantic meaning of "integer" and can lead to invalid data being passed to AWS CloudFormation. Port numbers, Unix timestamps, and other integer fields cannot have fractional values.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,10 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Reject non-integer floats
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
+        return int_val
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
-    else:
-        return x
```