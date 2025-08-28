# Bug Report: troposphere Empty Title Validation Bypass

**Target**: `troposphere.BaseAWSObject.validate_title()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-19

## Summary

Empty string titles bypass validation in troposphere AWS objects due to a logic error that skips validation for falsy title values.

## Property-Based Test

```python
from troposphere import certificatemanager
import pytest

def test_empty_title_should_be_rejected():
    """Empty title should raise ValueError due to validation."""
    with pytest.raises(ValueError, match="not alphanumeric"):
        certificatemanager.Certificate(
            title="",
            DomainName="example.com"
        )
```

**Failing input**: Empty string `""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import certificatemanager

cert = certificatemanager.Certificate(
    title="",
    DomainName="example.com"
)
print(f"Certificate created with empty title: '{cert.title}'")
dict_repr = cert.to_dict()
print(f"Resource type: {dict_repr['Type']}")
```

## Why This Is A Bug

The `validate_title()` method contains logic to reject empty titles with the condition `if not self.title or not valid_names.match(self.title)`. However, this validation is never called for empty strings because line 183 in `__init__.py` checks `if self.title:` before calling `validate_title()`. Empty strings are falsy in Python, so validation is bypassed entirely. This allows invalid CloudFormation resource names to be created.

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