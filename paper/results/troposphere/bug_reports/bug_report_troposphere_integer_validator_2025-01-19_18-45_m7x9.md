# Bug Report: troposphere Integer Validator Accepts Float Values

**Target**: `troposphere.validators.integer()`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-01-19

## Summary

The `integer()` validator function incorrectly accepts float values without raising an error, violating the expected type contract for integer properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import certificatemanager

@given(days=st.floats(min_value=0.1, max_value=999.9).filter(lambda x: x != int(x)))
def test_integer_property_rejects_floats(days):
    """Integer properties should reject float values."""
    with pytest.raises((ValueError, TypeError)):
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry=days
        )
        account = certificatemanager.Account(
            title="TestAccount",
            ExpiryEventsConfiguration=config
        )
        account.to_dict()
```

**Failing input**: `3.14`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import certificatemanager

config = certificatemanager.ExpiryEventsConfiguration(
    DaysBeforeExpiry=3.14
)
account = certificatemanager.Account(
    title="TestAccount",
    ExpiryEventsConfiguration=config
)
dict_repr = account.to_dict()
print(f"DaysBeforeExpiry value: {dict_repr['Properties']['ExpiryEventsConfiguration']['DaysBeforeExpiry']}")
print(f"Type: {type(dict_repr['Properties']['ExpiryEventsConfiguration']['DaysBeforeExpiry'])}")
```

## Why This Is A Bug

The `integer()` validator function is meant to ensure values are valid integers, but it accepts float values like `3.14`. The function only attempts `int(x)` to check if conversion is possible, but returns the original value unchanged. This allows float values to pass through when integer types are expected, potentially causing issues downstream when CloudFormation expects integer values.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,11 +45,14 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    # Reject float values that are not whole numbers
+    if isinstance(x, float) and not x.is_integer():
+        raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```