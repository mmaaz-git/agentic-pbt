# Bug Report: troposphere.sso Title Validation Ignores validation Parameter

**Target**: `troposphere.sso.Application` (and all AWSObject subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validation=False` parameter in AWSObject constructors does not bypass title validation, preventing creation of CloudFormation resources with non-alphanumeric titles even when validation is explicitly disabled.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import troposphere.sso as sso
import string

arbitrary_string_strategy = st.text(min_size=0, max_size=255)

@given(title=arbitrary_string_strategy)  
def test_title_validation_consistency(title):
    """Test that title validation respects the validation parameter"""
    
    assume(len(title) > 0)
    
    # With validation=False, any title should be accepted
    app = sso.Application(title, validation=False, Name='test')
    
    # The object should be created successfully
    assert app.title == title
```

**Failing input**: `':'`

## Reproducing the Bug

```python
import troposphere.sso as sso

# This should work with validation=False but raises ValueError
app = sso.Application(':', validation=False, Name='test')
```

## Why This Is A Bug

The `validation` parameter in the AWSObject constructor is documented to control validation behavior, but title validation is always enforced regardless of this parameter. The code shows:

```python
def __init__(self, title, template=None, validation=True, **kwargs):
    self.title = title
    self.do_validation = validation
    # ...
    # try to validate the title if its there
    if self.title:
        self.validate_title()  # Always called, ignores do_validation
```

This violates the API contract where `validation=False` should disable validation checks. CloudFormation allows non-alphanumeric characters in logical resource names (e.g., with `::` for nested stacks), but troposphere prevents creating such resources even when validation is disabled.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,9 @@ class AWSObject(BaseAWSObject):
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.do_validation:
+            if self.title:
+                self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```