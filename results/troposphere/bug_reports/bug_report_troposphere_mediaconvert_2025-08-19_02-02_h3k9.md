# Bug Report: troposphere.mediaconvert Title Validation Bypass

**Target**: `troposphere.mediaconvert` (affects all troposphere AWS resources)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty strings and None values bypass title validation in troposphere AWS resources, violating the documented alphanumeric-only requirement and potentially causing issues in CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.mediaconvert as mc

@given(title=st.one_of(st.just(""), st.just(None)))
def test_invalid_titles_should_be_rejected(title):
    """Test that empty/None titles are rejected per regex validation"""
    try:
        jt = mc.JobTemplate(title, SettingsJson={})
        assert False, f"Invalid title {title!r} was accepted"
    except (ValueError, TypeError):
        pass  # Expected behavior
```

**Failing input**: `""` (empty string) and `None`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Template
from troposphere.mediaconvert import JobTemplate

jt_empty = JobTemplate("", SettingsJson={"key": "value"})
print(f"Created JobTemplate with empty title: {jt_empty.title!r}")

jt_none = JobTemplate(None, SettingsJson={"key": "value"})
print(f"Created JobTemplate with None title: {jt_none.title!r}")

template = Template()
jt_in_template = JobTemplate("", template=template, SettingsJson={})
print(f"Added resource with empty title to template: {'' in template.resources}")

import troposphere
print(f"Regex requires alphanumeric: {troposphere.valid_names.pattern}")
print(f"Empty string matches regex: {bool(troposphere.valid_names.match(''))}")
```

## Why This Is A Bug

The troposphere library defines a validation regex `^[a-zA-Z0-9]+$` that requires titles to be non-empty alphanumeric strings. However, the validation is conditionally executed with `if self.title: self.validate_title()`, causing empty strings and None values to skip validation entirely. This violates the documented contract that resource names must be alphanumeric and can lead to invalid CloudFormation templates or unexpected behavior when resources have empty/None identifiers.

## Fix

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
         self.properties = {}
```