# Bug Report: troposphere Integer Validator Accepts Non-Integer Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator function accepts float values when it should only accept integers, violating the contract implied by its name and causing float values to be stored where integers are expected.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import macie
from troposphere.validators import integer

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
def test_integer_validator_rejects_floats(float_value):
    """The integer validator should reject non-integer float values"""
    with pytest.raises((TypeError, ValueError)):
        result = integer(float_value)
        # If it doesn't raise, check it at least converts to int
        assert isinstance(result, int), f"integer({float_value}) returned {result} of type {type(result)}"
```

**Failing input**: `1.1`

## Reproducing the Bug

```python
from troposphere import macie
from troposphere.validators import integer

# The integer validator accepts floats
result = integer(1.1)
print(f"integer(1.1) = {result}")  # Output: 1.1
print(f"Type: {type(result)}")     # Output: <class 'float'>

# This allows float values in supposedly integer-only fields
cdi = macie.CustomDataIdentifier(
    title="TestCDI",
    Name="TestName", 
    Regex=".*",
    MaximumMatchDistance=1.1  # Should be integer but accepts float
)

serialized = cdi.to_dict()
print(f"MaximumMatchDistance: {serialized['Properties']['MaximumMatchDistance']}")  # Output: 1.1
print(f"Type: {type(serialized['Properties']['MaximumMatchDistance'])}")            # Output: <class 'float'>
```

## Why This Is A Bug

The `integer` validator function is meant to ensure values are integers, as indicated by:
1. Its name "integer" clearly implies it validates integer types
2. It's used for properties documented as requiring integers (e.g., MaximumMatchDistance)
3. The function checks if the value can be converted to int but returns the original value unchanged

This causes CloudFormation templates to contain float values where integers are expected, which could lead to deployment failures or unexpected behavior.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       # Check if it's already an integer type or can be cleanly converted
+       if isinstance(x, bool):
+           # Booleans are technically integers in Python but should be rejected
+           raise ValueError("%r is not a valid integer" % x) 
+       elif isinstance(x, int):
+           return x
+       elif isinstance(x, float):
+           if x.is_integer():
+               return int(x)
+           else:
+               raise ValueError("%r is not a valid integer" % x)
+       else:
+           # Try converting strings and other types
+           converted = int(x)
+           return converted
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
-   else:
-       return x
```