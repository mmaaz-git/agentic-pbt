# Bug Report: troposphere Empty String Bypasses Title Validation

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The title validation method accepts empty strings despite using a regex pattern `^[a-zA-Z0-9]+$` that should require at least one alphanumeric character.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from troposphere.docdb import DBCluster
import re

@given(st.text())
@example("")
def test_title_validation_property(title):
    """Titles must match ^[a-zA-Z0-9]+$ (non-empty alphanumeric)"""
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    
    try:
        cluster = DBCluster(title)
        cluster.validate_title()
        if not pattern.match(title):
            raise AssertionError(f"Invalid title '{title}' passed validation")
    except ValueError:
        if pattern.match(title):
            raise AssertionError(f"Valid title '{title}' was rejected")
```

**Failing input**: `""`

## Reproducing the Bug

```python
from troposphere.docdb import DBCluster

cluster = DBCluster("")
cluster.validate_title()  # No error raised

import re
pattern = re.compile(r"^[a-zA-Z0-9]+$")
print(pattern.match(""))  # Returns None (doesn't match)
```

## Why This Is A Bug

The validation uses regex pattern `^[a-zA-Z0-9]+$` where `+` means "one or more" characters. However, the validation logic checks `if not self.title or not valid_names.match(self.title)`. The first condition `not self.title` evaluates to True for empty strings, causing the validation to skip the regex check entirely. This allows invalid CloudFormation resource names.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if not valid_names.match(self.title) if self.title else True:
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```