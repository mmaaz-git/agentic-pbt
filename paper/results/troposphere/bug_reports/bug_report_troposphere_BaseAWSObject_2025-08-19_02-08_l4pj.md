# Bug Report: BaseAWSObject Accepts Invalid Empty Titles

**Target**: `troposphere.BaseAWSObject`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

BaseAWSObject and its subclasses accept empty string and None as titles without validation, even though the validate_title() method requires alphanumeric characters matching the regex `^[a-zA-Z0-9]+$`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import string
import troposphere.mwaa as mwaa

@given(st.text())
def test_environment_title_validation(title):
    """Test that Environment title validation follows alphanumeric rules"""
    try:
        env = mwaa.Environment(title)
        # If it succeeds, title should be alphanumeric
        assert title is not None
        assert len(title) > 0
        assert all(c in string.ascii_letters + string.digits for c in title)
    except ValueError as e:
        # Should fail for non-alphanumeric titles
        if title:
            assert not all(c in string.ascii_letters + string.digits for c in title)
```

**Failing input**: `""`

## Reproducing the Bug

```python
import troposphere.mwaa as mwaa

# Empty string should be rejected but is accepted
env1 = mwaa.Environment("")
print(f"Created environment with empty title: '{env1.title}'")

# None should be rejected but is accepted
env2 = mwaa.Environment(None)
print(f"Created environment with None title: {env2.title}")

# For comparison, non-alphanumeric titles are correctly rejected
try:
    env3 = mwaa.Environment("test-name")
except ValueError as e:
    print(f"Non-alphanumeric correctly rejected: {e}")
```

## Why This Is A Bug

The `validate_title()` method enforces that titles must match `^[a-zA-Z0-9]+$`, which requires at least one alphanumeric character. However, the validation is skipped when the title is falsy (empty string or None) due to the condition `if self.title:` before calling `validate_title()`. This allows invalid resource names to be created, potentially causing issues when the CloudFormation template is deployed.

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