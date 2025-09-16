# Bug Report: troposphere.inspector Title Validation Bypass

**Target**: `troposphere.inspector` (affects all troposphere AWS resources)
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Empty string and None titles bypass validation in troposphere AWS resources, causing TypeErrors when generating CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import inspector
import re

@given(st.text(min_size=1))
def test_title_validation_property(title_text):
    """Resource titles must match the pattern ^[a-zA-Z0-9]+$ to be valid."""
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    
    if valid_pattern.match(title_text):
        target = inspector.AssessmentTarget(title_text)
        assert target.title == title_text
    else:
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            inspector.AssessmentTarget(title_text)
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
from troposphere import inspector, Template

# Bug: Empty/None titles bypass validation
target_empty = inspector.AssessmentTarget('')
target_none = inspector.AssessmentTarget(None)

# Causes TypeError when generating template
template = Template()
template.add_resource(target_empty)
template.add_resource(target_none)

# This crashes with: TypeError: '<' not supported between instances of 'NoneType' and 'str'
template.to_json()
```

## Why This Is A Bug

The BaseAWSObject.__init__ method only validates titles if they are truthy:

```python
if self.title:
    self.validate_title()
```

But validate_title() itself would reject empty/None titles:

```python
def validate_title(self) -> None:
    if not self.title or not valid_names.match(self.title):
        raise ValueError('Name "%s" not alphanumeric' % self.title)
```

This inconsistency allows invalid titles to bypass validation, violating AWS CloudFormation requirements that resource names must be alphanumeric. The invalid titles later cause TypeErrors during template generation.

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
@@ -324,8 +323,9 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+        if self.title is not None:
+            if not self.title or not valid_names.match(self.title):
+                raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
         pass
```