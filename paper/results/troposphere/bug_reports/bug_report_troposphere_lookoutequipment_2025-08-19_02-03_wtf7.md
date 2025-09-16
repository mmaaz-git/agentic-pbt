# Bug Report: troposphere.lookoutequipment Misleading Error Message for Title Validation

**Target**: `troposphere.lookoutequipment` (all classes)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation error message incorrectly states "not alphanumeric" for Unicode characters that Python considers alphanumeric, creating a misleading contract violation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.lookoutequipment as le

valid_titles = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)

@given(title=valid_titles)
def test_title_validation(title):
    config = le.S3InputConfiguration(
        title=title,
        Bucket='test-bucket'
    )
```

**Failing input**: `'µ'` (Greek letter mu)

## Reproducing the Bug

```python
import troposphere.lookoutequipment as le

char = 'µ'
print(f"Is '{char}' alphanumeric? {char.isalnum()}")  # True

config = le.S3InputConfiguration(
    title=char,
    Bucket='test-bucket'
)  # Raises: ValueError: Name "µ" not alphanumeric
```

## Why This Is A Bug

The error message states the character is "not alphanumeric" when Python's `isalnum()` returns `True`. CloudFormation requires ASCII alphanumeric characters only (A-Za-z0-9), which the regex correctly enforces, but the error message misleads users about what "alphanumeric" means in this context.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII alphanumeric characters (A-Za-z0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```