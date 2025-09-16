# Bug Report: troposphere.validators.integer Accepts Float Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `integer()` validator function incorrectly accepts float values without raising an error, violating its intended purpose of validating integer inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
def test_integer_rejects_floats(value):
    try:
        integer(value)
        assert False, f"Expected ValueError for float {value}"
    except (ValueError, TypeError):
        pass
```

**Failing input**: `1.5`

## Reproducing the Bug

```python
from troposphere.validators import integer

result = integer(1.5)
print(f"integer(1.5) = {result}")
print(f"Type: {type(result)}")
```

## Why This Is A Bug

The `integer()` function is used to validate AWS CloudFormation properties that must be integers (e.g., `TargetDpus`, `BytesScannedCutoffPerQuery`). By accepting float values, it fails to properly validate inputs, potentially causing deployment failures or unexpected behavior when CloudFormation templates are processed by AWS. The function name clearly indicates it should validate integers, not accept floats.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,8 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
```