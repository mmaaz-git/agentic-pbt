# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Values

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer` validator incorrectly accepts non-integer float and Decimal values, returning them unchanged instead of rejecting them. This violates the validator's contract and can lead to invalid AWS CloudFormation templates.

## Property-Based Test

```python
from decimal import Decimal
from hypothesis import given, strategies as st
import troposphere.validators as validators

@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_integer_validator_rejects_non_integers(value):
    """Integer validator should only accept integer values"""
    if value == int(value):  # Is integer-valued
        result = validators.integer(value)
        assert result == value
    else:  # Non-integer decimal
        with pytest.raises(ValueError):
            validators.integer(value)
```

**Failing input**: `Decimal('0.5')`

## Reproducing the Bug

```python
from decimal import Decimal
import troposphere.validators as validators
import troposphere.validators.elasticsearch as es_validators

# Bug 1: integer validator accepts non-integers
result = validators.integer(Decimal('0.5'))
print(f"integer(Decimal('0.5')) = {result}")  # Returns 0.5, should raise ValueError

result = validators.integer(3.14)
print(f"integer(3.14) = {result}")  # Returns 3.14, should raise ValueError

# Bug 2: This propagates to derived validators
checker = es_validators.integer_range(0, 10)
result = checker(5.5)
print(f"integer_range(0,10)(5.5) = {result}")  # Returns 5.5, should raise ValueError

# Bug 3: Affects AWS CloudFormation validation
result = es_validators.validate_automated_snapshot_start_hour(12.5)
print(f"validate_automated_snapshot_start_hour(12.5) = {result}")  # Returns 12.5, invalid for CloudFormation
```

## Why This Is A Bug

The `integer` validator's purpose is to ensure values represent integers for AWS CloudFormation templates. However, it only checks if `int(x)` doesn't raise an exception, not if the value actually represents an integer. Since `int(float)` truncates rather than validates, non-integer values pass validation.

This causes:
1. Invalid CloudFormation templates when float values are accepted for integer-only properties
2. Silent data corruption through truncation semantics
3. Violation of the principle of least surprise - an "integer validator" should validate integers

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -10,7 +10,10 @@ def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # For numeric types, ensure the value is actually an integer
+        if hasattr(x, '__float__') or hasattr(x, '__int__'):
+            if x != int_val:
+                raise ValueError("%r is not an integer value" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
```