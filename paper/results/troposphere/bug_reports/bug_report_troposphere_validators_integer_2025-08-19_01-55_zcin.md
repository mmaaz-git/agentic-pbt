# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The integer validator incorrectly accepts non-integer float values like 0.5, 3.14, and -2.7, which silently lose precision when converted to integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
def test_integer_validator_rejects_non_integer_floats(value):
    """Test that integer validator rejects non-integer float values"""
    with pytest.raises(ValueError):
        integer(value)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
from troposphere.validators import integer

result1 = integer(0.5)
print(f"integer(0.5) = {result1}")  # Returns 0.5, should raise ValueError
print(f"int(0.5) = {int(0.5)}")      # Shows precision loss: returns 0

result2 = integer(3.14)
print(f"integer(3.14) = {result2}")  # Returns 3.14, should raise ValueError
print(f"int(3.14) = {int(3.14)}")    # Shows precision loss: returns 3

result3 = integer(-2.7)
print(f"integer(-2.7) = {result3}")  # Returns -2.7, should raise ValueError
print(f"int(-2.7) = {int(-2.7)}")    # Shows precision loss: returns -2
```

## Why This Is A Bug

The integer validator is meant to validate that a value is an integer, but it only checks if `int(x)` succeeds. Since `int()` can convert floats by truncating decimal parts, non-integer floats pass validation. This can lead to silent data loss when CloudFormation properties expecting integers receive float values that get truncated. The validator returns the original float value, which could cause type errors downstream or incorrect CloudFormation templates.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,9 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        # Check if it's a float with non-zero decimal part
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError("%r is not an integer" % x)
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
```