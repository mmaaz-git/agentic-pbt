# Bug Report: troposphere.validators.boolean Accepts Complex Numbers

**Target**: `troposphere.validators.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator incorrectly accepts complex numbers with zero imaginary parts (e.g., `0j`, `1+0j`) and converts them to boolean values, violating the expected contract of only accepting specific boolean representations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators

@given(st.complex_numbers())
def test_boolean_validator_rejects_complex_numbers(value):
    """Boolean validator should reject all complex numbers"""
    try:
        result = troposphere.validators.boolean(value)
        assert False, f"Should have raised ValueError for complex number {value}"
    except ValueError:
        pass  # Expected behavior
```

**Failing input**: `0j` (also `1+0j`)

## Reproducing the Bug

```python
import troposphere.validators
import troposphere.servicecatalog as sc

# Direct validator test
result1 = troposphere.validators.boolean(0j)
print(f"boolean(0j) = {result1}")  # Returns False (should raise ValueError)

result2 = troposphere.validators.boolean(1+0j)  
print(f"boolean(1+0j) = {result2}")  # Returns True (should raise ValueError)

# Real-world impact on CloudFormation resources
product = sc.CloudFormationProduct(
    'TestProduct',
    Name='MyProduct',
    Owner='MyOwner',
    ReplaceProvisioningArtifacts=0j  # Complex number accepted!
)
print(product.to_dict()['Properties']['ReplaceProvisioningArtifacts'])  # False
```

## Why This Is A Bug

The boolean validator's documentation and intended use is to accept specific boolean representations: `True`, `False`, `1`, `0`, `"1"`, `"0"`, `"true"`, `"false"`, `"True"`, `"False"`. Complex numbers are not documented as valid inputs and their acceptance is due to Python's equality comparison behavior where `0j == 0` and `1+0j == 1`. This allows unintended types to pass validation, potentially leading to confusion and incorrect CloudFormation templates.

## Fix

```diff
def boolean(x: Any) -> bool:
+    # Reject complex numbers explicitly
+    if isinstance(x, complex):
+        raise ValueError
     if x in [True, 1, "1", "true", "True"]:
         return True
     if x in [False, 0, "0", "false", "False"]:
         return False
     raise ValueError
```