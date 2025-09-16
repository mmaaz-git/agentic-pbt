# Bug Report: troposphere.validators Integer Validator Accepts and Returns Float Values

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The integer validator accepts float values and returns them as floats instead of converting to integers or rejecting them, violating the expected behavior for integer validation in CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import pytest
import troposphere.msk as msk

@given(
    invalid_value=st.floats()
)  
def test_integer_property_type_enforcement(invalid_value):
    """Test that integer properties reject or convert float values"""
    config = msk.ConfigurationInfo(
        Arn="arn:aws:kafka:us-east-1:123456789012:configuration/test",
        Revision=invalid_value
    )
    result = config.to_dict()
    # Should either reject floats or convert to int
    assert isinstance(result['Revision'], int)
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
from troposphere.validators import integer
import troposphere.msk as msk
import json

# Direct validator test
result = integer(123.5)
print(f"integer(123.5) = {result}")     # 123.5
print(f"type: {type(result)}")          # <class 'float'>

# Impact on CloudFormation resources
config = msk.ConfigurationInfo(
    Arn="arn:aws:kafka:us-east-1:123456789012:configuration/test",
    Revision=123.5
)
output = config.to_dict()
print(json.dumps(output))
# {"Arn": "...", "Revision": 123.5}
```

## Why This Is A Bug

The integer validator should either:
1. Convert float values to integers (losing precision)
2. Reject float values entirely

Currently it accepts floats and passes them through unchanged, causing CloudFormation templates to contain float values where AWS expects integers. This violates AWS CloudFormation's type requirements and the validator's implied contract.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    # Reject floats that aren't whole numbers
+    if isinstance(x, float) and not x.is_integer():
+        raise ValueError("%r is not a valid integer" % x)
+    # Convert whole number floats to int
+    if isinstance(x, float):
+        return int(x)
     else:
         return x
```