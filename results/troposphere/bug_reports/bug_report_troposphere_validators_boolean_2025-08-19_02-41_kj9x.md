# Bug Report: troposphere.validators.boolean Accepts Unintended Numeric Types

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` validator incorrectly accepts float, Decimal, and complex number types when their values equal 0 or 1, violating its documented contract of only accepting specific bool, int, and string values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest

@given(st.one_of(
    st.floats(),
    st.complex_numbers(),
    st.decimals(allow_nan=False, allow_infinity=False)
))
def test_boolean_rejects_numeric_types(value):
    """Boolean validator should reject float/complex/decimal types"""
    from troposphere.validators import boolean
    
    # These types should not be accepted
    if value not in [True, False, 0, 1]:
        with pytest.raises(ValueError):
            boolean(value)
```

**Failing input**: `0.0` (float)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean
from decimal import Decimal

# These should all raise ValueError but don't
invalid_values = [0.0, 1.0, Decimal('0'), Decimal('1'), 0j, 1+0j]

for value in invalid_values:
    result = boolean(value)
    print(f"boolean({value!r}) = {result}")
```

## Why This Is A Bug

The `boolean` function's implementation checks if values are in lists using Python's `in` operator, which uses equality comparison (`==`). Since `0.0 == 0` and `1.0 == 1` evaluate to `True` in Python, these numeric types incorrectly pass validation.

According to the function's documentation and usage context (CloudFormation template validation), only the following values should be accepted:
- `True`, `False` (bool)
- `0`, `1` (int)
- `"true"`, `"True"`, `"false"`, `"False"`, `"0"`, `"1"` (str)

Accepting float, Decimal, or complex types could lead to unexpected behavior in CloudFormation templates.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if type(x) in [bool, int, str] and x in [True, 1, "1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if type(x) in [bool, int, str] and x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```