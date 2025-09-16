# Bug Report: troposphere.validators.integer Accepts Float Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` validator function incorrectly accepts float values with decimal parts, returning them unchanged instead of raising a ValueError as expected for non-integer inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_validator_rejects_float_values(value):
    """The integer validator should reject non-integer float values."""
    with pytest.raises(ValueError):
        integer(value)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
from troposphere import mediaconnect

# Bug 1: integer() accepts float values
result = integer(0.5)
print(f"integer(0.5) = {result}")  # Returns 0.5 instead of raising ValueError

# Bug 2: This allows invalid CloudFormation templates
output = mediaconnect.BridgeNetworkOutput(
    IpAddress="192.168.1.1",
    NetworkName="test",
    Port=8080.5,  # Invalid port number accepted
    Protocol="tcp",
    Ttl=255
)
print(f"Port stored as: {output.properties['Port']}")  # 8080.5
```

## Why This Is A Bug

1. The function name `integer()` clearly indicates it should only accept integer values
2. The error message "is not a valid integer" confirms non-integers should be rejected
3. This allows invalid CloudFormation templates with float Port numbers (e.g., 8080.5)
4. AWS CloudFormation expects integer values for properties defined as `integer` type

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,11 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check if the value is actually an integer (not a float with decimals)
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```