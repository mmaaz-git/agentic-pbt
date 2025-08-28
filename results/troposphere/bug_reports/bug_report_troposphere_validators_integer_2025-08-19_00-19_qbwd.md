# Bug Report: troposphere.validators Integer Validator Accepts Float Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator in troposphere accepts float values when it should reject them, violating the expected contract of an integer validator.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
def test_integer_validator_rejects_floats(value):
    """Property: integer validator rejects non-integer numbers"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(value)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import integer

# Test shows integer validator incorrectly accepts floats
result = integer(0.5)
print(f"integer(0.5) = {result}")  # Returns 0.5 instead of raising ValueError
print(f"Type: {type(result)}")     # <class 'float'>

# This affects real usage - ConfigurationId.Revision should only accept integers
from troposphere.amazonmq import ConfigurationId
config = ConfigurationId(Id="test", Revision=1.5)  # Should fail but doesn't
print(config.to_dict())  # {'Id': 'test', 'Revision': 1.5}
```

## Why This Is A Bug

The `integer` validator is used to ensure properties that should be integers (like `ConfigurationId.Revision` in amazonmq) only accept integer values. Currently, it accepts any value that can be converted to int via `int()`, rather than validating that the value IS an integer. This violates the principle of least surprise and the documented purpose of an integer validator.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        # Check if value is already an integer or integer-like string
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError("%r is not a valid integer" % x)
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
```