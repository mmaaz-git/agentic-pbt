# Bug Report: troposphere.opensearchserverless Misleading Title Validation Error Message

**Target**: `troposphere.opensearchserverless` (and all troposphere modules)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The error message for title validation incorrectly states "not alphanumeric" when rejecting Unicode alphanumeric characters that Python's `str.isalnum()` considers valid.

## Property-Based Test

```python
@given(st.text(min_size=1))
def test_title_validation_alphanumeric(title):
    """Test that resource titles must be alphanumeric."""
    is_alphanumeric = title.isalnum()
    
    try:
        ap = oss.AccessPolicy(
            title=title,
            Name="test",
            Policy="{}",
            Type="data"
        )
        # If we got here, title was accepted
        assert is_alphanumeric, f"Non-alphanumeric title '{title}' was incorrectly accepted"
    except ValueError as e:
        # Title was rejected
        assert not is_alphanumeric, f"Alphanumeric title '{title}' was incorrectly rejected"
        assert "not alphanumeric" in str(e)
```

**Failing input**: `'¹'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.opensearchserverless as oss

title = "Collection¹"
print(f"Is '{title}' alphanumeric? {title.isalnum()}")  # Prints: True

collection = oss.Collection(
    title=title,
    Name="test-collection"
)  # Raises: ValueError: Name "Collection¹" not alphanumeric
```

## Why This Is A Bug

The error message "not alphanumeric" is semantically incorrect. Python's `str.isalnum()` returns `True` for Unicode alphanumeric characters including superscripts (¹²³), subscripts (₁₂₃), accented characters (áéñü), and non-Latin scripts (αβγ, 一二三). However, troposphere only accepts ASCII alphanumeric characters [A-Za-z0-9] as required by AWS CloudFormation.

The validation logic is correct (AWS CloudFormation requires ASCII-only), but the error message misleads users who may expect Unicode support based on Python's standard definition of "alphanumeric".

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