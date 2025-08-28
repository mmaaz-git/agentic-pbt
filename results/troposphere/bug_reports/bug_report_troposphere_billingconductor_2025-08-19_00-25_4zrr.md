# Bug Report: troposphere.billingconductor Missing Validation in from_dict()

**Target**: `troposphere.billingconductor.BillingGroup.from_dict()`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` method in troposphere AWS resource classes fails to validate required properties, allowing creation of invalid CloudFormation resources that only fail when `to_dict()` is called.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.billingconductor import BillingGroup

@given(st.sampled_from(["Name", "PrimaryAccountId", "AccountGrouping", "ComputationPreference"]))
def test_from_dict_validates_required_fields(missing_field):
    valid_dict = {
        "Name": "TestGroup",
        "PrimaryAccountId": "123456789012",
        "AccountGrouping": {"LinkedAccountIds": ["123456789012"]},
        "ComputationPreference": {"PricingPlanArn": "arn:aws:pricing::123456789012:plan/test"}
    }
    
    incomplete_dict = valid_dict.copy()
    del incomplete_dict[missing_field]
    
    # This should raise an error but doesn't
    bg = BillingGroup.from_dict("TestBG", incomplete_dict)
    
    # The error only happens here, too late
    bg.to_dict()  # Raises ValueError
```

**Failing input**: Any dict missing required fields like `{"Name": "TestGroup"}` (missing PrimaryAccountId, AccountGrouping, ComputationPreference)

## Reproducing the Bug

```python
from troposphere.billingconductor import BillingGroup

# Create BillingGroup without required fields - should fail but doesn't
bg = BillingGroup.from_dict("InvalidBG", {})
print("Bug: Created invalid BillingGroup from empty dict")

# The validation only happens when converting back to dict
try:
    bg.to_dict()
except ValueError as e:
    print(f"Validation delayed until to_dict(): {e}")
```

## Why This Is A Bug

This violates the fail-fast principle. Invalid CloudFormation resources can be created and passed around in code, only failing when serialized. This could lead to runtime errors in production when invalid templates are generated, making debugging difficult.

## Fix

The validation logic in `_validate_props()` should be called during `from_dict()` construction, not just in `to_dict()`:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -401,6 +401,8 @@ class BaseAWSObject:
         if title:
             return cls(title, **props)
-        return cls(**props)
+        obj = cls(**props)
+        obj._validate_props()  # Validate immediately after creation
+        return obj
```