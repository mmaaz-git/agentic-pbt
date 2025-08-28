# Bug Report: troposphere.validators Double Validator Accepts Infinity and NaN

**Target**: `troposphere.validators.double`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double` validator accepts special float string values like 'Inf', '-Inf', and 'NaN', which cannot be properly serialized to JSON for CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import double

@given(st.sampled_from(['Inf', '-Inf', 'inf', '-inf', 'Infinity', 'NaN', 'nan']))
def test_double_validator_rejects_special_floats(x):
    """Test that double validator rejects infinity and NaN strings"""
    with pytest.raises(ValueError, match="is not a valid double"):
        double(x)
```

**Failing input**: `'Inf'`

## Reproducing the Bug

```python
from troposphere.validators import double
import json

result = double('Inf')
print(f"double('Inf') = {result}")  # Returns 'Inf'
print(f"float(result) = {float(result)}")  # Returns inf

result = double('NaN')
print(f"double('NaN') = {result}")  # Returns 'NaN'
print(f"float(result) = {float(result)}")  # Returns nan

# These values cannot be serialized to JSON
try:
    json.dumps(float('inf'))
except ValueError as e:
    print(f"JSON serialization fails: {e}")
```

## Why This Is A Bug

CloudFormation templates are serialized to JSON, which does not support Infinity, -Infinity, or NaN values. Accepting these values in the validator will cause:

1. CloudFormation template generation to fail during JSON serialization
2. Invalid CloudFormation templates if custom serialization is used
3. Unexpected behavior when AWS processes these values

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -93,7 +93,10 @@ def integer_list_item_checker(
 
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        float(x)
+        f = float(x)
+        import math
+        if math.isinf(f) or math.isnan(f):
+            raise ValueError
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x
```