# Bug Report: troposphere.validators Integer Validator Accepts Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The integer validator incorrectly accepts float values, returning them unchanged instead of rejecting them or converting them to integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import pytest
from troposphere.validators import integer

@given(st.floats())
def test_integer_validator_rejects_floats(value):
    """Integer validator should reject float values."""
    assume(not value.is_integer())  # Skip integer-valued floats like 1.0
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(value)
```

**Failing input**: `value=3.14`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
from troposphere import codedeploy

result = integer(3.14)
print(f"integer(3.14) = {result!r} (type: {type(result)})")
print(f"Expected: ValueError")
print(f"Actual: Accepts float and returns 3.14")

tbc = codedeploy.TimeBasedCanary(
    CanaryInterval=3.14,
    CanaryPercentage=50.5
)
print(f"\nTimeBasedCanary.to_dict() = {tbc.to_dict()}")
print("CloudFormation expects integers but receives floats!")
```

## Why This Is A Bug

The integer validator is meant to validate that values are integers, but it only checks if `int(x)` doesn't raise an exception. This allows float values to pass through unchanged, violating the API contract that properties validated with `integer` should be integer values. CloudFormation expects integer types for integer-typed properties.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,11 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
-    except (ValueError, TypeError):
+        int_val = int(x)
+        # Reject floats that aren't exact integers
+        if isinstance(x, float) and (x != int_val or not x.is_integer()):
+            raise ValueError
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```