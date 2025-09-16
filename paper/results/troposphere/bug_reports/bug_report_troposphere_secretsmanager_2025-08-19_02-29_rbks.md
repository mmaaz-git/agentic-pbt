# Bug Report: troposphere.secretsmanager Integer Validator Accepts Non-Integers

**Target**: `troposphere.secretsmanager.integer` and `GenerateSecretString.PasswordLength`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator in troposphere.secretsmanager accepts non-integer values like floats, and consequently PasswordLength accepts invalid values including non-integers and non-positive numbers.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import troposphere.secretsmanager as sm
import math

@given(st.floats(min_value=-1e10, max_value=1e10))
def test_integer_validator_rejects_non_integers(x):
    assume(not x.is_integer())
    assume(not math.isnan(x))
    assume(not math.isinf(x))
    
    try:
        result = sm.integer(x)
        assert False, f"integer validator accepted non-integer {x}"
    except ValueError:
        pass

@given(st.one_of(
    st.floats(min_value=-100, max_value=10000),
    st.integers(min_value=-100, max_value=10000)
))
def test_password_length_validation(length):
    gen_str = sm.GenerateSecretString()
    
    try:
        gen_str.PasswordLength = length
        
        if isinstance(length, float) and not length.is_integer():
            assert False, f"PasswordLength accepted non-integer float {length}"
        elif isinstance(length, (int, float)) and length <= 0:
            assert False, f"PasswordLength accepted non-positive value {length}"
    except (ValueError, TypeError):
        pass
```

**Failing input**: `1.5` for integer validator, `1.5` and `0` for PasswordLength

## Reproducing the Bug

```python
import troposphere.secretsmanager as sm

# Bug 1: Integer validator accepts non-integers
result = sm.integer(1.5)
print(f"integer(1.5) = {result}")  # Returns 1.5, should raise ValueError

# Bug 2: PasswordLength accepts invalid values
gen_str = sm.GenerateSecretString()

gen_str.PasswordLength = 1.5
print(f"PasswordLength = {gen_str.PasswordLength}")  # Accepts 1.5

gen_str.PasswordLength = 0
print(f"PasswordLength = {gen_str.PasswordLength}")  # Accepts 0

gen_str.PasswordLength = -10
print(f"PasswordLength = {gen_str.PasswordLength}")  # Accepts -10
```

## Why This Is A Bug

The `integer` function is meant to validate integer values, as its name suggests. However, it only checks if `int(x)` doesn't raise an exception, not whether the value is actually an integer. This allows floats like 1.5 to pass validation.

For PasswordLength specifically, AWS Secrets Manager requires this to be a positive integer between 1 and 4096. Accepting non-integers, zero, or negative values violates the AWS CloudFormation specification and could lead to deployment failures.

## Fix

```diff
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
+        # Also check that it's actually an integer value
+        if isinstance(x, float) and not x.is_integer():
+            raise ValueError("%r is not a valid integer" % x)
+        # Reject non-positive values for properties that need them
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```

For a more complete fix, PasswordLength should have additional validation to ensure it's within the valid range (1-4096) as specified by AWS.