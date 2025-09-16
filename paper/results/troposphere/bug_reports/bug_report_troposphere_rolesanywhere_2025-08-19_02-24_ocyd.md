# Bug Report: troposphere.rolesanywhere Validation Inconsistency

**Target**: `troposphere.rolesanywhere`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate()` method in troposphere.rolesanywhere classes does not check required properties, but `to_dict()` does, leading to inconsistent validation behavior.

## Property-Based Test

```python
import troposphere.rolesanywhere as ra
import pytest

def test_validation_inconsistency():
    """Test that validate() and to_dict() have inconsistent validation"""
    # CRL has required properties: CrlData and Name
    crl = ra.CRL('TestCRL')  # Missing both required properties
    
    # validate() incorrectly passes
    crl.validate()  # No exception raised (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        crl.to_dict()
    assert "CrlData required" in str(exc.value)
```

**Failing input**: Creating any AWS object without its required properties

## Reproducing the Bug

```python
import troposphere.rolesanywhere as ra

# Create a CRL object without required properties
crl = ra.CRL('TestCRL')

# The validate() method should fail but doesn't
crl.validate()
print("validate() passed (BUG: should have failed!)")

# The to_dict() method correctly fails
try:
    crl.to_dict()
except ValueError as e:
    print(f"to_dict() failed with: {e}")
```

## Why This Is A Bug

This violates the expected contract of the `validate()` method. Users expect `validate()` to ensure an object is valid before proceeding. The inconsistency means:
1. Objects that pass `validate()` can still fail when converted to dictionaries
2. The validation logic is split across two methods instead of being centralized
3. Users cannot rely on `validate()` to catch configuration errors early

This affects all AWS resource classes in the module: CRL, Profile, and TrustAnchor.

## Fix

The `validate()` method should call `_validate_props()` to check required properties, just like `to_dict()` does:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -320,6 +320,7 @@ class BaseAWSObject(object):
     def validate(self) -> None:
         if self.validation:
             self.validate_title()
+            self._validate_props()
             validated = []
             for k, (_, required) in self.props.items():
                 if required and k not in self.properties:
```