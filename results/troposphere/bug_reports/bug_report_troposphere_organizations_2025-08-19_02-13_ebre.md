# Bug Report: troposphere.organizations Empty Title Validation Bypass

**Target**: `troposphere.organizations` (BaseAWSObject.validate_title)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty strings bypass title validation in troposphere AWS resources, violating the documented alphanumeric requirement that titles must match `^[a-zA-Z0-9]+$`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import organizations
import re

@given(title=st.one_of(
    st.just(""),
    st.just(None),
    st.text(min_size=1).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))
))
def test_organization_title_edge_cases(title):
    try:
        org = organizations.Organization(title=title)
        dict_repr = org.to_dict()
        
        # Empty title should fail validation
        if title == "":
            assert False, "Empty title should have been rejected"
        
        # None title should work - it's allowed
        if title is None:
            assert org.title is None
        else:
            # Valid alphanumeric title
            assert org.title == title
            
    except ValueError as e:
        # Should only fail for empty string
        if title == "":
            assert 'not alphanumeric' in str(e)
        else:
            raise  # Unexpected error
```

**Failing input**: `title=""`

## Reproducing the Bug

```python
from troposphere import organizations

org = organizations.Organization(title="")
print(f"Title accepted: {repr(org.title)}")
print(f"Dict representation: {org.to_dict()}")
```

## Why This Is A Bug

The `validate_title` method in BaseAWSObject checks if titles match the regex pattern `^[a-zA-Z0-9]+$`, which requires at least one alphanumeric character. Empty strings do not match this pattern and should be rejected. However, the validation is skipped for empty strings due to a logic error in the initialization code (line 183 of `__init__.py`):

```python
if self.title:  # Empty string evaluates to False, skipping validation
    self.validate_title()
```

This allows empty titles to bypass validation entirely, violating the documented contract that titles must be alphanumeric.

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