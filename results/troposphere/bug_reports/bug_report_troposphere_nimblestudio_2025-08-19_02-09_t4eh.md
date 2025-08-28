# Bug Report: troposphere.nimblestudio Title Validation Unicode Mismatch

**Target**: `troposphere.nimblestudio.StudioComponent` (and all AWSObject/AWSProperty classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Title validation in troposphere uses an ASCII-only regex pattern that rejects valid Unicode alphanumeric characters that Python's `isalnum()` accepts, causing an inconsistency in validation logic.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.nimblestudio as nimblestudio

@given(title=st.text())
def test_title_validation(title):
    """Test that title validation works correctly."""
    try:
        component = nimblestudio.StudioComponent(
            title=title,
            Name="TestName",
            StudioId="TestStudio",
            Type="SHARED_FILE_SYSTEM"
        )
        assert title.isalnum() or title == ""
    except ValueError as e:
        if "not alphanumeric" in str(e):
            assert not title.isalnum() or title == ""
        else:
            raise
```

**Failing input**: `'¹'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.nimblestudio as nimblestudio

test_char = '¹'
print(f"Python isalnum(): {test_char.isalnum()}")  # True

component = nimblestudio.StudioComponent(
    title=test_char,
    Name="TestName",
    StudioId="TestStudio",
    Type="SHARED_FILE_SYSTEM"
)  # Raises ValueError: Name "¹" not alphanumeric
```

## Why This Is A Bug

The validation logic uses `valid_names = re.compile(r"^[a-zA-Z0-9]+$")` which only matches ASCII alphanumeric characters, but Python's `isalnum()` returns True for Unicode alphanumeric characters like superscripts (¹²³), Greek letters (αβγ), Roman numerals (ⅠⅡⅢ), and accented letters (ÀÉÑ). This creates an inconsistent validation behavior where the error message claims a character is "not alphanumeric" when Python considers it alphanumeric.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -67,7 +67,7 @@ PARAMETER_TITLE_MAX: Final[int] = 255
 MAX_RESOURCES: Final[int] = 500
 PARAMETER_TITLE_MAX: Final[int] = 255
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[a-zA-Z0-9]+$", re.ASCII)
 
 def is_aws_object_subclass(cls: Any) -> bool:
     is_aws_object = False
@@ -324,7 +324,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" not ASCII alphanumeric (must match [a-zA-Z0-9]+)' % self.title)
 
     def validate(self) -> None:
         pass
```