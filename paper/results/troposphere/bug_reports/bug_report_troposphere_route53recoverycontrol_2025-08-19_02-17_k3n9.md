# Bug Report: troposphere.route53recoverycontrol Empty Title Validation Bypass

**Target**: `troposphere.route53recoverycontrol` (and all `troposphere.BaseAWSObject` subclasses)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty string titles bypass validation in troposphere AWS resource classes, allowing creation of resources with invalid empty titles that should be rejected.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.route53recoverycontrol as r53rc

@given(st.text())
def test_title_validation(title):
    """Test that title validation works correctly"""
    valid = title and all(c.isalnum() for c in title)
    
    try:
        cluster = r53rc.Cluster(title=title, Name="TestName")
        assert valid, f"Invalid title '{title}' was accepted"
    except ValueError:
        assert not valid or not title, f"Valid title '{title}' was rejected"
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import troposphere.route53recoverycontrol as r53rc

# Empty string title bypasses validation
cluster = r53rc.Cluster(title="", Name="TestName")
print(f"Created cluster with invalid empty title: '{cluster.title}'")

# Validation would reject it if called directly
try:
    cluster.validate_title()
except ValueError as e:
    print(f"Direct validation correctly rejects: {e}")
```

## Why This Is A Bug

The `validate_title()` method correctly rejects empty strings as invalid (not matching `^[a-zA-Z0-9]+$`). However, the validation is only triggered when `self.title` is truthy in `BaseAWSObject.__init__()`. Since empty strings are falsy in Python, validation is skipped entirely for empty string titles, violating the documented constraint that titles must be alphanumeric.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
+        if self.title is not None:
             self.validate_title()
 
         # Create the list of properties set on this object by the user
```