# Bug Report: troposphere.datasync Title Validation Inconsistency

**Target**: `troposphere.datasync` (affects all troposphere AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere incorrectly rejects Unicode alphanumeric characters (e.g., Greek letters, mathematical symbols) despite the error message claiming they are "not alphanumeric". These characters are considered alphanumeric by Python's standard `str.isalnum()` method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.datasync as datasync

@given(
    cls=st.sampled_from([datasync.Agent]),
    title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)
)
def test_title_validation(cls, title):
    """Test that alphanumeric titles are accepted."""
    if title.isalnum():
        obj = cls(title=title)  # Should not raise for alphanumeric strings
        assert obj.title == title
```

**Failing input**: `'µ'` (Greek letter mu)

## Reproducing the Bug

```python
import troposphere.datasync as datasync

title = 'µ'
print(f"Is '{title}' alphanumeric according to Python? {title.isalnum()}")

try:
    agent = datasync.Agent(title=title)
    print("Title accepted")
except ValueError as e:
    print(f"Title rejected: {e}")
```

## Why This Is A Bug

The validation regex pattern `^[a-zA-Z0-9]+$` only accepts ASCII alphanumeric characters, but the error message "not alphanumeric" is misleading because these Unicode characters ARE alphanumeric according to Python's standard definition. This creates a contract violation where:

1. The error message implies a broader definition of "alphanumeric"
2. Python developers expect `str.isalnum()` compatibility
3. The actual implementation is more restrictive than documented

## Fix

Either update the error message to be accurate or expand the validation to accept all Unicode alphanumeric characters:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and digits' % self.title)
```

Or alternatively, accept all alphanumeric characters:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if not self.title or not self.title.isalnum():
             raise ValueError('Name "%s" not alphanumeric' % self.title)
```