# Bug Report: troposphere Title Validation Rejects Valid Unicode Alphanumeric Characters

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere uses an ASCII-only regex that rejects valid Unicode alphanumeric characters, causing an inconsistency with Python's definition of alphanumeric and limiting internationalization support.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.pinpointemail as pe

# Generate Unicode letters and digits
unicode_alphanumeric = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Lo', 'Lm')),
    min_size=1
).filter(lambda x: x.isalnum())

@given(title=unicode_alphanumeric)
def test_unicode_alphanumeric_titles(title):
    # Title that is alphanumeric according to Python should be accepted
    obj = pe.ConfigurationSet(title=title, Name="TestConfig")
    obj.validate_title()  # Should not raise
```

**Failing input**: `'µ'` (Greek letter mu), `'π'`, `'测试'`, `'café'`, and many other Unicode alphanumeric strings

## Reproducing the Bug

```python
import troposphere.pinpointemail as pe

title = 'µ'  # Greek letter mu
print(f"Is '{title}' alphanumeric? {title.isalnum()}")  # True

obj = pe.ConfigurationSet(title=title, Name="TestConfig")
# Raises: ValueError: Name "µ" not alphanumeric
```

## Why This Is A Bug

The error message states the title is "not alphanumeric", but Python's `isalnum()` returns `True` for these characters. The regex `^[a-zA-Z0-9]+$` only matches ASCII characters, creating an inconsistency with Python's broader Unicode support and the natural interpretation of "alphanumeric". This prevents users from using valid international characters in resource titles.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -67,7 +67,7 @@ MAX_RESOURCES: Final[int] = 500
 PARAMETER_TITLE_MAX: Final[int] = 255
 
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[\w]+$", re.UNICODE)
 
 
 def is_aws_object_subclass(cls: Any) -> bool:
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if not self.title or not self.title.replace('_', '').isalnum():
             raise ValueError('Name "%s" not alphanumeric' % self.title)
```