# Bug Report: troposphere.shield Title Validation Inconsistency

**Target**: `troposphere.shield` (BaseAWSObject.__init__ and validate_title)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Title validation is inconsistent between object initialization and the validate_title() method. Empty string and None titles bypass validation during __init__ but are correctly rejected by validate_title().

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import shield

@given(title=st.one_of(st.none(), st.text(max_size=10)))
def test_title_validation_consistency(title):
    """Test that title validation is consistent between __init__ and validate_title()."""
    
    try:
        obj = shield.DRTAccess(title, RoleArn='arn:aws:iam::123456789012:role/Test')
        created = True
    except (ValueError, TypeError) as e:
        created = False
    
    if created:
        try:
            obj.validate_title()
            validation_passed = True
        except ValueError as e:
            validation_passed = False
        
        assert validation_passed, (
            f"Inconsistent validation: __init__ accepted title {repr(title)} "
            f"but validate_title() rejected it"
        )
```

**Failing input**: `title=None` and `title=''`

## Reproducing the Bug

```python
from troposphere import shield

# Case 1: Empty string title
drt = shield.DRTAccess('', RoleArn='arn:aws:iam::123456789012:role/Test')
print(f"Created with title: {repr(drt.title)}")

try:
    drt.validate_title()
except ValueError as e:
    print(f"validate_title() rejects: {e}")

# Case 2: None title
drt2 = shield.DRTAccess(None, RoleArn='arn:aws:iam::123456789012:role/Test')
print(f"Created with title: {repr(drt2.title)}")

try:
    drt2.validate_title()
except ValueError as e:
    print(f"validate_title() rejects: {e}")
```

## Why This Is A Bug

The BaseAWSObject.__init__ method only calls validate_title() when `self.title` is truthy:

```python
if self.title:
    self.validate_title()
```

However, empty string and None are falsy in Python, so validation is skipped. This creates an inconsistency where:
1. Objects can be created with invalid titles (empty string or None)
2. These same titles are correctly rejected by validate_title()
3. The validation behavior is inconsistent depending on how it's triggered

This violates the principle that validation should be consistent regardless of when it's performed.

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
         self.properties = {}
```

This fix ensures validate_title() is called for all non-None titles, including empty strings, making validation consistent.