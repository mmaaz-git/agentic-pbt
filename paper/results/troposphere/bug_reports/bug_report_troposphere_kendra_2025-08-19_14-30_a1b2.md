# Bug Report: troposphere.kendra Unicode Digit Acceptance in Integer Validator

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The integer validator accepts Unicode digit strings (e.g., Thai "๗", Arabic "٧") which produce CloudFormation templates with Unicode characters that AWS services cannot parse correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer
import troposphere.kendra as kendra

@given(st.sampled_from(["๗", "੭", "೭", "٧", "१"]))
def test_unicode_digits_should_be_rejected(unicode_digit):
    """Unicode digits should be rejected or converted to ASCII"""
    result = integer(unicode_digit)
    # Bug: Returns the Unicode string unchanged
    assert result == unicode_digit
    
    # This creates invalid CloudFormation
    config = kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=unicode_digit,
        StorageCapacityUnits=7
    )
    # Produces {"QueryCapacityUnits": "\u0e57", "StorageCapacityUnits": 7}
```

**Failing input**: Unicode digit string "๗" (Thai digit seven)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.kendra as kendra
import json

thai_seven = "๗"
result = integer(thai_seven)
print(f"integer('{thai_seven}') = {repr(result)}")

config = kendra.CapacityUnitsConfiguration(
    QueryCapacityUnits=thai_seven,
    StorageCapacityUnits=7
)

cf_json = json.dumps(config.to_dict())
print(f"CloudFormation JSON: {cf_json}")
```

## Why This Is A Bug

The integer validator's purpose is to ensure values are valid integers for CloudFormation. While Python's `int()` can parse Unicode digits, CloudFormation and AWS services expect ASCII digit strings or numeric values. Accepting Unicode digits creates templates that will fail during deployment.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       # Convert to int and back to ensure ASCII digits only
+       if isinstance(x, str):
+           int_val = int(x)
+           # Ensure the string representation matches
+           if str(int_val) != x.strip():
+               raise ValueError("%r contains non-ASCII digits or formatting" % x)
+       else:
+           int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```