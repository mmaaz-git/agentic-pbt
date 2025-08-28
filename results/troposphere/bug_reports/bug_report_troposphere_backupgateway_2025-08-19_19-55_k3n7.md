# Bug Report: troposphere.backupgateway Empty Title Validation Bypass

**Target**: `troposphere.backupgateway.Hypervisor`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The Hypervisor class in troposphere.backupgateway accepts empty strings as titles, allowing creation of invalid CloudFormation templates that AWS will reject.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import backupgateway

@given(title=st.text(min_size=0, max_size=1))
def test_title_validation_enforced(title):
    """Test that invalid titles are rejected during object creation or serialization"""
    if not title or not title.replace(' ', '').replace('\n', ''):  # Empty or whitespace
        # Should either fail on creation or during to_dict()
        try:
            h = backupgateway.Hypervisor(title)
            result = h.to_dict()
            # If we get here with empty title, that's a bug
            assert title and title.strip(), f"Empty title '{title}' was accepted"
        except ValueError:
            pass  # Expected for invalid titles
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import backupgateway

h = backupgateway.Hypervisor('')
h.Host = '10.0.0.1'
h.Name = 'MyHypervisor'

template_dict = h.to_dict()
print(f"Generated dict: {template_dict}")
print("This creates an invalid CloudFormation template with empty logical ID")

try:
    h.validate_title()
    print("ERROR: validate_title() passed")
except ValueError as e:
    print(f"validate_title() correctly rejects: {e}")
```

## Why This Is A Bug

CloudFormation requires logical IDs (resource names) to be non-empty alphanumeric strings. The troposphere library has a `validate_title()` method that correctly checks this requirement, but it's never called during normal object usage. This allows invalid templates to be generated that will fail when deployed to AWS.

The validation chain `__init__` → `to_dict()` → `validate()` never calls `validate_title()`, even though the method exists and works correctly.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -327,7 +327,10 @@ class BaseAWSObject:
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
-        pass
+        # Validate title if object has one
+        if hasattr(self, 'title') and self.title is not None:
+            self.validate_title()
+        # Subclasses can add additional validation
 
     def no_validation(self: __BaseAWSObjectTypeVar) -> __BaseAWSObjectTypeVar:
         self.do_validation = False
```