# Bug Report: troposphere.analytics Empty Title Validation Bypass

**Target**: `troposphere.analytics.Application` and all other AWSObject classes
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Empty strings and None values bypass title validation in troposphere AWSObject classes, violating the documented requirement that titles must be alphanumeric.

## Property-Based Test

```python
@given(st.text())
def test_title_validation(title):
    """Test that title validation correctly accepts only alphanumeric titles"""
    try:
        app = analytics.Application(title)
        # If it succeeds, title should be alphanumeric
        assert re.match(r'^[a-zA-Z0-9]+$', title) is not None
    except ValueError as e:
        # If it fails, title should NOT be alphanumeric
        if 'not alphanumeric' in str(e):
            assert re.match(r'^[a-zA-Z0-9]+$', title) is None
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import analytics

app = analytics.Application("")
print(f"Created Application with invalid empty title: '{app.title}'")

app2 = analytics.Application(None)
print(f"Created Application with None title: {app2.title}")
```

## Why This Is A Bug

The title validation regex `^[a-zA-Z0-9]+$` requires at least one alphanumeric character, but the validation is skipped for falsy values (empty string, None) due to the conditional check `if self.title:` before calling `validate_title()`. This allows invalid titles to be created, violating the alphanumeric requirement enforced for all other title values.

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
@@ -324,7 +323,7 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is not None and (not self.title or not valid_names.match(self.title)):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```