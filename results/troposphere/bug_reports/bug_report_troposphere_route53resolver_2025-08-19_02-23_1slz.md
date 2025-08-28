# Bug Report: troposphere.route53resolver Integer Validator Accepts Floats

**Target**: `troposphere.route53resolver` (specifically `troposphere.validators.integer`)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts float values with decimal parts, allowing invalid CloudFormation templates to be generated for properties that require integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import pytest
import troposphere.route53resolver as r53r

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_rejects_floats_with_decimal_parts(x):
    """The integer() function should reject floats with decimal parts"""
    assume(not x.is_integer())  # Only test non-integer floats
    
    with pytest.raises(ValueError, match="is not a valid integer"):
        r53r.integer(x)
```

**Failing input**: `1.5`

## Reproducing the Bug

```python
import troposphere.route53resolver as r53r

# The integer validator accepts floats with decimal parts
result = r53r.integer(1.5)
print(f"integer(1.5) = {result}")  # Returns 1.5 instead of raising ValueError

# This allows invalid CloudFormation to be generated
rule = r53r.FirewallRule()
rule.Priority = 1.5  # Should reject float, but accepts it
print(f"FirewallRule.Priority = {rule.Priority}")  # 1.5

# Generated CloudFormation will be invalid
print(rule.to_dict())  # {'Priority': 1.5, ...}
```

## Why This Is A Bug

The `integer()` function is used to validate properties that AWS CloudFormation expects to be integers (Priority, BlockOverrideTtl, InstanceCount). By accepting floats, troposphere generates invalid CloudFormation templates that will be rejected by AWS. The function's name and purpose clearly indicate it should only accept integer values.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
+       # Ensure the value is actually an integer, not just convertible to int
+       if isinstance(x, float) and not x.is_integer():
+           raise ValueError
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```