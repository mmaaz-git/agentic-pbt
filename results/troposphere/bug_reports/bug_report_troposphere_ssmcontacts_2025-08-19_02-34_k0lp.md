# Bug Report: troposphere.ssmcontacts integer() Function Doesn't Convert to Integer

**Target**: `troposphere.ssmcontacts.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` function validates that a value can be converted to integer but returns the original value unchanged, allowing float values to pass through to integer-typed CloudFormation fields.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ssmcontacts as ssmcontacts

@given(st.floats(min_value=-1000, max_value=1000).filter(lambda x: not x.is_integer()))
def test_integer_function_should_convert_floats(x):
    result = ssmcontacts.integer(x)
    
    # Bug: returns float unchanged instead of converting to int
    assert result == x
    assert isinstance(result, float)
```

**Failing input**: `10.5`

## Reproducing the Bug

```python
import troposphere.ssmcontacts as ssmcontacts

# The integer() function should convert to int or reject non-integers
result = ssmcontacts.integer(10.5)
print(f"integer(10.5) = {result}")  # Output: 10.5
print(f"type: {type(result)}")      # Output: <class 'float'>

# Impact on AWS resources
stage = ssmcontacts.Stage(DurationInMinutes=25.7)
stage_dict = stage.to_dict()
print(stage_dict)  # Output: {'DurationInMinutes': 25.7}
# CloudFormation receives float 25.7 instead of integer 25
```

## Why This Is A Bug

The function is named `integer()` and is used to validate integer-typed fields in AWS CloudFormation templates. It validates that `int(x)` doesn't raise an error but returns the original value unchanged. This allows float values like `10.5` to be passed to CloudFormation for fields that expect integers, potentially causing deployment failures or unexpected behavior.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       return int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
-   else:
-       return x
```