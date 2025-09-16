# Bug Report: troposphere.s3tables Integer Validator Accepts Floats with Fractional Parts

**Target**: `troposphere.s3tables.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator function incorrectly accepts float values with fractional parts (e.g., 1.5, 2.7) when it should only accept whole numbers.

## Property-Based Test

```python
import math
from hypothesis import given, strategies as st
import troposphere.s3tables as s3t


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_property(x):
    """
    Property: The integer validator should only accept values that represent
    whole numbers (integers), and reject values with fractional parts.
    """
    is_whole_number = x == math.floor(x)
    
    try:
        result = s3t.integer(x)
        assert is_whole_number, f"integer() accepted {x} which has fractional part {x - math.floor(x)}"
        assert result == x
    except ValueError:
        assert not is_whole_number, f"integer() rejected {x} which is a whole number"
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import troposphere.s3tables as s3t

result = s3t.integer(1.5)
print(f"integer(1.5) = {result}")

obj = s3t.UnreferencedFileRemoval(
    NoncurrentDays=1.5,
    UnreferencedDays=2.7,
    Status='Enabled'
)
print(f"Properties: {obj.properties}")
```

## Why This Is A Bug

The `integer()` function is a validator meant to ensure values are integers, as indicated by its name. However, it accepts any value for which `int(x)` doesn't raise an exception, including floats with fractional parts. This allows invalid CloudFormation templates to be generated with non-integer values for properties like `NoncurrentDays` and `UnreferencedDays` which must be integers in AWS CloudFormation.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
+       # Also check that the value is actually an integer (no fractional part)
+       if isinstance(x, float) and not x.is_integer():
+           raise ValueError("%r is not a valid integer" % x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```