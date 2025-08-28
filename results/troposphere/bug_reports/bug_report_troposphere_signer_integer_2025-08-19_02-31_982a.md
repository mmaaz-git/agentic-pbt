# Bug Report: troposphere.signer Integer Validation Accepts Non-Integer Floats

**Target**: `troposphere.signer.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts non-integer float values like 1.5, allowing invalid values to propagate to CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.signer as signer

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_function_rejects_non_integers(x):
    try:
        result = signer.integer(x)
        int_val = int(result)
        if isinstance(x, float):
            assert x == float(int_val), f"integer() accepted non-integer float {x}"
    except (ValueError, TypeError):
        if isinstance(x, (int, float)):
            assert x != float(int(x)), f"integer() rejected valid integer {x}"
```

**Failing input**: `1.5`

## Reproducing the Bug

```python
import troposphere.signer as signer

result = signer.integer(1.5)
print(f"integer(1.5) = {result}")  # Returns 1.5 instead of raising ValueError

svp = signer.SignatureValidityPeriod(Type='Days', Value=365.5)
print(svp.to_dict())  # {'Type': 'Days', 'Value': 365.5}
```

## Why This Is A Bug

The `integer()` function is meant to validate that values are integers before they're used in CloudFormation templates. AWS CloudFormation expects integer values for fields like SignatureValidityPeriod.Value. Accepting float values like 365.5 days could cause CloudFormation deployment failures or unexpected behavior. The function currently only checks if `int(x)` succeeds, but doesn't verify that the value is actually an integer.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
+   # Check that float values are actually integers
+   if isinstance(x, float) and not x.is_integer():
+       raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```