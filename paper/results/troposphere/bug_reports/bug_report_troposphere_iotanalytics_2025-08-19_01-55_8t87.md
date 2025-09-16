# Bug Report: troposphere.iotanalytics Title Validation Inconsistency

**Target**: `troposphere.iotanalytics` (applies to all troposphere resources)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Troposphere's title validation rejects Unicode alphanumeric characters while claiming to validate "alphanumeric" names, creating an inconsistency between the error message and actual behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import iotanalytics

@given(title=st.text(min_size=1, max_size=100))
def test_invalid_resource_title_validation(title):
    """Test that resource titles are properly validated"""
    try:
        channel = iotanalytics.Channel(title)
        assert title.isalnum(), f"Non-alphanumeric title accepted: {title}"
        assert channel.title == title
    except ValueError as e:
        assert not title.isalnum() or not title, f"Alphanumeric title rejected: {title}"
        assert "not alphanumeric" in str(e)
```

**Failing input**: `'¹'` (superscript 1 character)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import iotanalytics

char = '¹'
print(f"Python isalnum(): {char.isalnum()}")  # True
try:
    channel = iotanalytics.Channel(char)
    print("Troposphere: ACCEPTED")
except ValueError as e:
    print(f"Troposphere: REJECTED ({e})")  # Name "¹" not alphanumeric
```

## Why This Is A Bug

The validation regex `^[a-zA-Z0-9]+$` only matches ASCII alphanumeric characters, but the error message claims to validate "alphanumeric" characters. Python's `isalnum()` returns `True` for many Unicode characters including:
- Superscripts: ¹ ² ³
- Greek letters: α β γ
- Accented letters: ñ ü é
- Other scripts: 一 二 א ب

This creates a contract violation where the error message promises alphanumeric validation but actually enforces ASCII-only validation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -67,7 +67,8 @@
 PARAMETER_TITLE_MAX: Final[int] = 255
 
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+# CloudFormation resource names must be ASCII alphanumeric only
+valid_names = re.compile(r"^[a-zA-Z0-9]+$")
 
 
 def is_aws_object_subclass(cls: Any) -> bool:
@@ -325,7 +326,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and numbers' % self.title)
 
     def validate(self) -> None:
         pass
```