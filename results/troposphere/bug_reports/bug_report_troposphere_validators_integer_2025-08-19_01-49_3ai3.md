# Bug Report: troposphere.validators Integer Validator Accepts Floats Causing Data Loss

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer` validator function accepts float values without raising an error, silently passing them through and causing data loss when later converted to integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_validator_rejects_floats(x):
    """Test that integer validator rejects non-integer floats"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(x)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(0.5)
print(f"integer(0.5) = {result}")  # Returns 0.5 (float)
print(f"int(result) = {int(result)}")  # Returns 0 - data loss!

result = integer(3.14159)
print(f"integer(3.14159) = {result}")  # Returns 3.14159
print(f"int(result) = {int(result)}")  # Returns 3 - data loss!
```

## Why This Is A Bug

The `integer` validator is supposed to validate that a value is a valid integer. It currently only checks that the value can be converted to int without error, but doesn't verify the value IS an integer. This causes:

1. Silent data loss when float values are truncated (0.5 becomes 0)
2. Type confusion - the validator returns floats when integers are expected
3. Potential CloudFormation template errors when float values are serialized

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,10 +45,12 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        if isinstance(x, float) and x != int_val:
+            raise ValueError
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```