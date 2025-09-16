# Bug Report: troposphere.controltower Title Validation Bypass

**Target**: `troposphere.controltower` (and all troposphere AWS resource classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere AWS resource classes fails to validate empty strings and None values, allowing invalid titles that violate the documented alphanumeric requirement.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.controltower import EnabledBaseline
import re

@given(title=st.text())
def test_title_validation(title):
    """Test that title validation works as documented"""
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    
    if valid_pattern.match(title):
        # Should not raise
        baseline = EnabledBaseline(
            title,
            BaselineIdentifier="id",
            BaselineVersion="1.0",
            TargetIdentifier="target"
        )
        assert baseline.title == title
    else:
        # Should raise ValueError for invalid titles
        try:
            baseline = EnabledBaseline(
                title,
                BaselineIdentifier="id", 
                BaselineVersion="1.0",
                TargetIdentifier="target"
            )
            assert False, f"Invalid title '{title}' was accepted"
        except ValueError:
            pass  # Expected
```

**Failing input**: `title=''` (empty string)

## Reproducing the Bug

```python
from troposphere.controltower import EnabledBaseline

# Empty string title should be rejected but isn't
baseline1 = EnabledBaseline(
    "",
    BaselineIdentifier="arn:aws:controltower:us-east-1::baseline/ABC123",
    BaselineVersion="1.0",
    TargetIdentifier="arn:aws:organizations::123456789012:ou/o-example/ou-example"
)
print(f"Empty title accepted: '{baseline1.title}'")

# None title should also be rejected but isn't
baseline2 = EnabledBaseline(
    None,
    BaselineIdentifier="arn:aws:controltower:us-east-1::baseline/ABC123", 
    BaselineVersion="1.0",
    TargetIdentifier="arn:aws:organizations::123456789012:ou/o-example/ou-example"
)
print(f"None title accepted: {baseline2.title}")
```

## Why This Is A Bug

The code explicitly validates titles with a regex pattern `^[a-zA-Z0-9]+$` requiring alphanumeric characters only. However, the validation is bypassed due to a falsy check in `troposphere/__init__.py` line 183-184:

```python
if self.title:
    self.validate_title()
```

Empty strings and None are falsy in Python, so they skip validation entirely. This violates the contract that CloudFormation resource names must be alphanumeric, potentially causing downstream errors when templates are deployed.

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
@@ -324,8 +324,11 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+        if self.title is None:
+            raise ValueError('Name cannot be None')
+        if not isinstance(self.title, str) or not self.title:
+            raise ValueError('Name must be a non-empty string')
+        if not valid_names.match(self.title):
+            raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
         pass
```