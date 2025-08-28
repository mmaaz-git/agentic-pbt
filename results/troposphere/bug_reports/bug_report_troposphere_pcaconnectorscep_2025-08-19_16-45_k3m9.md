# Bug Report: troposphere.pcaconnectorscep Empty/None Title Validation Bypass

**Target**: `troposphere.pcaconnectorscep` (applies to all troposphere AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Troposphere accepts empty strings and None as CloudFormation resource logical IDs (titles), bypassing validation that would correctly reject these invalid values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.pcaconnectorscep as pcaconnectorscep

@given(empty_str=st.just(""))
def test_empty_title_validation(empty_str):
    """Empty strings should be rejected as titles"""
    challenge = pcaconnectorscep.Challenge(empty_str, ConnectorArn="arn:test")
    challenge.to_dict()  # Should raise ValueError but doesn't
```

**Failing input**: `empty_str=""` and also `None`

## Reproducing the Bug

```python
import troposphere.pcaconnectorscep as pcaconnectorscep

# Bug 1: Empty string accepted
challenge_empty = pcaconnectorscep.Challenge("", ConnectorArn="arn:test")
result = challenge_empty.to_dict()
print(f"Empty title accepted: {result}")

# Bug 2: None accepted
challenge_none = pcaconnectorscep.Challenge(None, ConnectorArn="arn:test")
result = challenge_none.to_dict()  
print(f"None title accepted: {result}")

# The validation method works but isn't called
try:
    challenge_empty.validate_title()
except ValueError as e:
    print(f"Direct validation correctly rejects empty: {e}")
```

## Why This Is A Bug

CloudFormation logical resource IDs must be non-empty alphanumeric strings. Accepting empty/None titles creates invalid templates that will fail at deployment. The validate_title() method correctly rejects these values, but is conditionally skipped during initialization.

## Fix

The bug is in `troposphere/__init__.py` line 183-184. The validation is conditionally called only for truthy titles:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,7 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        self.validate_title()
 
         # Create the list of properties set on this object by the user
```

Alternative fix preserving optional titles for AWSProperty:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,9 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
+        if self.title is not None:  # Validate even empty strings
             self.validate_title()
+        # Note: AWSProperty allows None titles, AWSObject does not
 
         # Create the list of properties set on this object by the user
```