# Bug Report: troposphere.validators.integer Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator accepts float values with fractional parts (e.g., 1.1, 2.5) without raising an error, violating the contract implied by its name and potentially causing issues in CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.kinesisvideo import SignalingChannel
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_validator_rejects_non_integers(value):
    """The integer validator should reject non-integer floats."""
    with pytest.raises(ValueError):
        integer(value)
```

**Failing input**: `1.1`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.kinesisvideo import SignalingChannel
from troposphere.validators import integer

# Bug: integer validator accepts float with fractional part
result = integer(1.1)
print(f"integer(1.1) = {result}")  # Returns 1.1 (float)

# This allows invalid values in AWS resources
channel = SignalingChannel("Test", MessageTtlSeconds=300.7)
print(f"MessageTtlSeconds = {channel.MessageTtlSeconds}")  # Stores 300.7

# Generated CloudFormation will have non-integer value
print(channel.to_dict()['Properties'])  # {'MessageTtlSeconds': 300.7}
```

## Why This Is A Bug

The `integer` validator's name and purpose indicate it should only accept integer values. However, it currently accepts any value that can be converted to int via `int()`, including floats with fractional parts. This violates the principle of least surprise and could lead to:

1. CloudFormation templates with non-integer values where integers are expected
2. Silent data loss through truncation (300.7 becomes 300)
3. Inconsistent behavior compared to other validation frameworks

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,6 +45,9 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
+        # Check if it's a float with fractional part
+        if isinstance(x, float) and x != int(x):
+            raise ValueError("%r is not an integer (has fractional part)" % x)
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
```