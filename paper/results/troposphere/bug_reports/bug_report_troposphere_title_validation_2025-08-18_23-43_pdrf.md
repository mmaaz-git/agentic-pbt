# Bug Report: troposphere Title Validation Unicode Inconsistency

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Title validation rejects Unicode alphanumeric characters that Python's `isalnum()` accepts, causing inconsistent behavior between the validation regex and Python's string methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.apprunner as apprunner

@given(st.text())
def test_title_validation_property(title):
    """Test that resource titles only accept alphanumeric characters"""
    try:
        resource = apprunner.Service(title)
        assert title.isalnum() and len(title) > 0
    except ValueError as e:
        assert not (title.isalnum() and len(title) > 0)
        assert 'not alphanumeric' in str(e)
```

**Failing input**: `'ª'` (ordinal indicator character)

## Reproducing the Bug

```python
import troposphere.apprunner as apprunner

char = 'ª'
print(f"Python isalnum(): {char.isalnum()}")  # True

try:
    resource = apprunner.Service(char)
    print("Success")
except ValueError as e:
    print(f"Failed: {e}")  # Name "ª" not alphanumeric
```

## Why This Is A Bug

The validation regex `^[a-zA-Z0-9]+$` only accepts ASCII alphanumeric characters, while Python's `isalnum()` method returns True for Unicode alphanumeric characters like 'ª', '¹', 'À', etc. This creates an inconsistency where characters that are considered alphanumeric by Python standards are rejected by troposphere's validation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -67,7 +67,7 @@
 PARAMETER_TITLE_MAX: Final[int] = 255
 
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[a-zA-Z0-9]+$", re.ASCII)
 
 
 def is_aws_object_subclass(cls: Any) -> bool:
@@ -325,7 +325,8 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" not alphanumeric (ASCII letters and digits only)' % self.title)
```