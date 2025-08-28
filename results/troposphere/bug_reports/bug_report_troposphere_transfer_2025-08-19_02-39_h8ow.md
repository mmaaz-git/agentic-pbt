# Bug Report: troposphere.transfer Unicode Digit Validation Bypass

**Target**: `troposphere.transfer.double` and `troposphere.transfer.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double()` and `integer()` validation functions accept non-ASCII Unicode digits (e.g., Arabic-Indic digits ٠-٩) and return them unchanged, which would cause AWS CloudFormation to reject or misinterpret the values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.transfer as transfer
import pytest

@given(st.sampled_from(["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"]))
def test_validators_reject_unicode_digits(x):
    """Validators should reject non-ASCII Unicode digits for CloudFormation compatibility"""
    with pytest.raises(ValueError):
        transfer.double(x)
    with pytest.raises(ValueError):
        transfer.integer(x)
```

**Failing input**: `'١'` (Arabic-Indic digit one)

## Reproducing the Bug

```python
import troposphere.transfer as transfer
import json

arabic_number = "١٢٣"  # Arabic-Indic for "123"

result = transfer.double(arabic_number)
print(f"Input: {arabic_number!r}")
print(f"Output: {result!r}")

cloudformation_json = json.dumps({"Value": result})
print(f"CloudFormation JSON: {cloudformation_json}")
# Output: {"Value": "\u0661\u0662\u0663"} instead of {"Value": "123"}
```

## Why This Is A Bug

The validators are meant to ensure values are valid for AWS CloudFormation templates. AWS CloudFormation expects numeric values as ASCII digits (0-9), not Unicode digits. Accepting Arabic-Indic digits creates invalid CloudFormation templates that AWS would reject.

## Fix

```diff
def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
+    # Ensure string inputs only contain ASCII digits
+    if isinstance(x, str) and any(c.isdigit() and not c.isascii() for c in x):
+        raise ValueError("%r contains non-ASCII digits" % x)
     try:
         float(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x


def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    # Ensure string inputs only contain ASCII digits
+    if isinstance(x, str) and any(c.isdigit() and not c.isascii() for c in x):
+        raise ValueError("%r contains non-ASCII digits" % x)
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```