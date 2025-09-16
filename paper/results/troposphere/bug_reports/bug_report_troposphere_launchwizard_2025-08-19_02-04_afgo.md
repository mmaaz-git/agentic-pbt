# Bug Report: troposphere.launchwizard Empty Title Validation Bypass

**Target**: `troposphere.launchwizard.Deployment`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Empty string titles bypass validation during object initialization but fail when `validate_title()` is called directly, creating inconsistent validation behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import launchwizard

@given(st.just(""))
def test_empty_title_validation_inconsistency(title):
    # Empty title passes initialization
    deployment = launchwizard.Deployment(
        title,
        DeploymentPatternName="pattern",
        Name="name", 
        WorkloadName="workload"
    )
    assert deployment.title == ""
    
    # But fails direct validation
    try:
        deployment.validate_title()
        assert False, "validate_title() should reject empty title"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)
```

**Failing input**: `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import launchwizard

deployment = launchwizard.Deployment(
    "",  # Empty title bypasses validation
    DeploymentPatternName="MyPattern",
    Name="MyDeployment",
    WorkloadName="MyWorkload"
)

print(f"Created deployment with empty title: {repr(deployment.title)}")

deployment.validate_title()  # This raises ValueError
```

## Why This Is A Bug

The `__init__` method only validates the title if it's truthy (`if self.title: self.validate_title()`), allowing empty strings and `None` to bypass validation. This creates inconsistent behavior where invalid titles can be created but fail later validation. CloudFormation resource names should not be empty.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```