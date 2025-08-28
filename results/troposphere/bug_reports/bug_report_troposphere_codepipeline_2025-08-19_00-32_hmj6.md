# Bug Report: troposphere.codepipeline Unicode Title Validation Error

**Target**: `troposphere.codepipeline` (all classes with title validation)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere incorrectly rejects Unicode alphanumeric characters while claiming they are "not alphanumeric", even though Python's standard `isalnum()` returns True for these characters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.codepipeline as cp

@given(title=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=50))
def test_title_validation_unicode(title):
    """Test that alphanumeric Unicode titles are accepted"""
    artifact = cp.ArtifactDetails(
        title=title,
        MaximumCount=1,
        MinimumCount=0
    )
    assert artifact.title == title
```

**Failing input**: `'µ'` (and many other Unicode letters like 'π', 'α', 'ñ', etc.)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codepipeline as cp

test_char = 'µ'
print(f"Is '{test_char}' alphanumeric? {test_char.isalnum()}")  # True

artifact = cp.ArtifactDetails(
    title=test_char,
    MaximumCount=1,
    MinimumCount=0
)
```

## Why This Is A Bug

The library's error message claims the character is "not alphanumeric" but this is incorrect. The character 'µ' (and many other Unicode letters) ARE alphanumeric according to Python's standard definition. The regex `^[a-zA-Z0-9]+$` only accepts ASCII characters, contradicting the error message which claims to check for "alphanumeric" characters in general.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -67,7 +67,7 @@ PARAMETER_TITLE_MAX: Final[int] = 255
 MAX_RESOURCES: Final[int] = 500
 
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[a-zA-Z0-9]+$")  # Keep ASCII-only for AWS compatibility
 
 
 def is_aws_object_subclass(cls: Any) -> bool:
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and digits (a-z, A-Z, 0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```